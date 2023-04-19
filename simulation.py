import numpy as np

from system_objects import Warehouse, Order


class Event:
    def __init__(self, event_type, event_start, event_obj):
        self.event_type = event_type
        self.event_start = event_start
        self.event_obj = event_obj

    def __repr__(self):
        return str(self.event_type) + ' ' + str(self.event_start) + ' ' + str(self.event_obj)


class Simulation:
    def __init__(self, time_limit, robot_num, order_enter_rate, warmup_dur=0.1):
        self.curr_time = 0
        self.time_limit = time_limit
        self.warmup_dur = warmup_dur
        self.order_enter_rate = order_enter_rate

        self.warehouse = Warehouse(r_amount=robot_num)
        self.events_lst = []
        self.empty_spots = []
        self.setup_instance()

        self.orders_in_sys_queue = []
        self.times_lst = [self.curr_time]
        self.order_cnt_lst = [0]
        self.served_orders = []
        self.served_orders_while_warmup = 0

    def setup_instance(self):
        self.warehouse.build_warehouse()
        first_event_start_time = np.random.exponential(1.0 / self.order_enter_rate)
        first_order = Order(first_event_start_time, np.random.randint(self.warehouse.number_of_types), status='queue')
        self.events_lst.append(Event('order', first_event_start_time, first_order))
        return

    def run_simulation(self):
        is_end_warm_up = False
        while self.curr_time < self.time_limit:
            self.perform_curr_event()
            if self.curr_time >= self.warmup_dur * self.time_limit and not is_end_warm_up:
                is_end_warm_up = True
                self.served_orders_while_warmup = len(self.served_orders)

    def perform_curr_event(self):
        self.events_lst.sort(key=lambda event: event.event_start)
        curr_event = self.events_lst.pop(0)
        self.curr_time = curr_event.event_start

        if curr_event.event_type == 'order':
            self.perform_event_order(curr_event)

        elif curr_event.event_type == 'robot_lifts_pod':
            self.perform_event_lift(curr_event)

        elif curr_event.event_type == 'robot_brings_pod_to_ws':
            self.perform_event_arrive_ws(curr_event)

        elif curr_event.event_type == 'finished_picking':
            self.perform_picking_finish(curr_event)

        elif curr_event.event_type == 'robot_puts_pod_down':
            self.perform_event_store(curr_event)
        return

    def perform_event_order(self, curr_event):
        self.times_lst.append(self.curr_time)
        self.order_cnt_lst.append(self.order_cnt_lst[-1] + 1)

        # Handle current Order
        curr_order = curr_event.event_obj
        avail_robots = self.warehouse.find_available_robots()
        item_in_order = curr_order.o_item
        avail_pods = self.warehouse.find_available_pods(item_type=item_in_order)
        if len(avail_robots) >= 1 and len(avail_pods) >= 1:
            curr_robot = avail_robots[0]
            # Sample pod number out of available pods
            pod_index = np.random.randint(len(avail_pods))
            # the selected pod object
            curr_pod = avail_pods[pod_index]
            arrival_to_pod_dur = curr_robot.assign_order_to_robot(curr_order, curr_pod)
            curr_pod.assign_order_to_robot()
            curr_order.assign_order_to_robot()
            arrival_to_pod_event = Event('robot_lifts_pod', self.curr_time + arrival_to_pod_dur, curr_robot)
            self.events_lst.append(arrival_to_pod_event)

        else:
            self.orders_in_sys_queue.append(curr_order)

        # Create a new Order arrival
        next_order_start = np.random.exponential(1.0 / self.order_enter_rate)
        next_order = Order(self.curr_time + next_order_start, np.random.randint(self.warehouse.number_of_types), status='queue')
        self.events_lst.append(Event('order', self.curr_time + next_order_start, next_order))

    def perform_event_lift(self, curr_event):
        curr_robot = curr_event.event_obj
        empty_spot = self.warehouse.release_pod_spot(curr_robot.r_pos)
        self.empty_spots.append(empty_spot)
        avail_workstations = self.warehouse.find_available_workstations()

        if len(avail_workstations) >= 1:
            curr_ws = avail_workstations[0]
            curr_ws.ws_occupied = True
        else:
            # no available ws, sample one
            curr_ws = np.random.choice(self.warehouse.ws_list)

        arrival_to_ws_dur = curr_robot.assign_robot_to_workstation(curr_ws)
        curr_pod = self.warehouse.find_pod_by_ind(curr_robot.r_occupied)
        curr_pod.assign_robot_to_workstation(curr_robot)
        curr_ws.assign_robot_to_workstation()

        arrival_to_ws_event = Event('robot_brings_pod_to_ws', self.curr_time + arrival_to_ws_dur, curr_robot)
        self.events_lst.append(arrival_to_ws_event)
        return

    def perform_event_arrive_ws(self, curr_event):
        curr_robot = curr_event.event_obj
        curr_ws = self.warehouse.find_ws_by_ind(curr_robot.r_ws)
        finish_picking_dur = curr_ws.assign_order_to_picking(curr_robot)
        if finish_picking_dur >= 0:
            finish_picking_event = Event('finished_picking', self.curr_time + finish_picking_dur, curr_robot)
            self.events_lst.append(finish_picking_event)
        return

    def perform_picking_finish(self, curr_event):
        curr_robot = curr_event.event_obj
        curr_ws = self.warehouse.find_ws_by_ind(curr_robot.r_ws)
        curr_pod = self.warehouse.find_pod_by_ind(curr_robot.r_occupied)
        curr_order = curr_robot.r_order

        # Finish service of Order
        curr_order.finish_service_order(self.curr_time)
        self.times_lst.append(self.curr_time)
        self.order_cnt_lst.append(self.order_cnt_lst[-1] - 1)
        self.served_orders.append(curr_order)

        # Start a new order
        res = curr_ws.serve_order_from_line()
        if res is not None:
            finish_picking_dur, next_robot = res
            finish_picking_event = Event('finished_picking', self.curr_time + finish_picking_dur, next_robot)
            self.events_lst.append(finish_picking_event)

        # Store the pod back
        empty_spot_ind = np.random.randint(len(self.empty_spots))
        store_spot_arr = self.empty_spots.pop(empty_spot_ind)
        empty_spot_loc = self.warehouse.keep_empty_spot(store_spot_arr[0], store_spot_arr[1])
        arrival_spot_dur = curr_robot.send_pod_to_store(empty_spot_loc)
        curr_pod.send_pod_to_store(empty_spot_loc)
        pod_store_event = Event('robot_puts_pod_down', self.curr_time + arrival_spot_dur, curr_robot)
        self.events_lst.append(pod_store_event)
        return

    def perform_event_store(self, curr_event):
        curr_robot = curr_event.event_obj
        curr_pod = self.warehouse.find_pod_by_ind(curr_robot.r_occupied)
        curr_robot.store_pod()
        curr_pod.store_pod()

        # Find new order to robot
        if len(self.orders_in_sys_queue) >= 1:
            for order_ind, order_obj in enumerate(self.orders_in_sys_queue):
                item_in_order = order_obj.o_item
                avail_pods = self.warehouse.find_available_pods(item_in_order)
                if len(avail_pods) >= 1:
                    self.orders_in_sys_queue.pop(order_ind)
                    # Sample pod number out of available pods
                    pod_index = np.random.randint(len(avail_pods))
                    # the selected pod object
                    curr_pod = avail_pods[pod_index]
                    arrival_to_pod_dur = curr_robot.assign_order_to_robot(order_obj, curr_pod)
                    curr_pod.assign_order_to_robot()
                    order_obj.assign_order_to_robot()
                    arrival_to_pod_event = Event('robot_lifts_pod', self.curr_time + arrival_to_pod_dur, curr_robot)
                    self.events_lst.append(arrival_to_pod_event)
                    break
        return


if __name__ == '__main__':
    simu_instance = Simulation(time_limit=604800*2, warmup_dur=0.1, robot_num=2, order_enter_rate=0.014 - 0.001)
    simu_instance.run_simulation()
