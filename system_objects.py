import numpy as np
from scipy.spatial import distance
import matplotlib.pyplot as plt
import pandas as pd

from utilis import calc_distance, calc_time_dur


class Robot:
    """
    #### Robot's class
    ##### attributes
    - x,y location
    - speed (1.3 m/s as default)
    - lifting & storing time (1 sec as default)
    - pod id (-1 if not carring a pod, else -pod's id)
    - work station id (-1 if not set for a ws, else - ws index)
    - r_order - the order which the robot is taking care of
    """
    def __init__(self, x, y, r_id, speed=1.3, l_time=1, s_time=1, pod_id=None, work_station=-1, r_order=None):
        self.r_speed = speed  # constant speed 1.3 m/s
        self.r_occupied = pod_id  # if None it's not occupied. else it's pod id
        self.r_ws = work_station  # if -1 not working for any workstation
        self.r_PodLiftTime = l_time
        self.r_PodStoreTime = s_time
        self.r_id = r_id
        self.r_pos = [x, y]
        self.r_order = r_order

    def __repr__(self):
        return str(self.r_id) + ' ' + ' is occupied?' + str(self.r_occupied)

    def is_free(self):
        return self.r_occupied is None

    def get_location(self):
        return self.r_pos

    def update_location(self, new_x, new_y):
        self.r_pos = [new_x, new_y]
        return

    def assign_order_to_robot(self, order_obj, pod_obj):
        self.r_order = order_obj
        self.r_occupied = pod_obj.pod_id
        dist = calc_distance(self.r_pos, [pod_obj.pod_x, pod_obj.pod_y])
        arrival_time_to_pod = calc_time_dur(dist, self.r_speed) + self.r_PodLiftTime
        self.update_location(pod_obj.pod_x, pod_obj.pod_y)
        return arrival_time_to_pod

    def assign_robot_to_workstation(self, workstation_obj):
        self.r_ws = workstation_obj.get_ind()
        if int(self.r_pos[1]) % 2 == 0:
            add_move = 1
        else:
            add_move = 0
        ws_loc = workstation_obj.get_location()
        dist = calc_distance(self.r_pos, ws_loc) + add_move
        arrival_time_ws = calc_time_dur(dist, self.r_speed)
        self.r_pos[0], self.r_pos[1] = ws_loc[0], ws_loc[1]
        return arrival_time_ws

    def send_pod_to_store(self, empty_spot_loc):
        dist = calc_distance(self.r_pos, empty_spot_loc)
        arrival_time_spot = calc_time_dur(dist, self.r_speed) + self.r_PodStoreTime
        self.update_location(empty_spot_loc[0], empty_spot_loc[1])
        return arrival_time_spot

    def store_pod(self):
        self.r_occupied = None
        return


class Order:
    """
    #### Order's class
    ##### attributes
    - enter time
    - exit time
    - item in order
    - status
    """
    def __init__(self, enter_time, item, status="queue", exit_time=None):
        self.o_enter_time = enter_time
        self.o_exit_time = exit_time
        self.o_item = item
        self.o_status = status  # can get queue, wip or done

    def __repr__(self):
        return str(self.o_item) + ' ' + str(self.o_enter_time) + " " + str(self.o_exit_time)

    def assign_order_to_robot(self):
        self.o_status = 'wip'
        return

    def finish_service_order(self, finish_time):
        self.o_exit_time = finish_time
        self.o_status = 'done'
        return


class WorkStation:
    """
    Workstation's class
    ##### attributes
    - x,y location
    - ws_id 0,1,2
    - picking_rate (1.0/15 as default)
    - orders - robot's list set to the ws with their order
    """
    def __init__(self, x, y, ws_id, picking_rate=1.0 / 15, orders=[]):
        self.ws_location = (x, y)
        self.ws_id = ws_id
        self.ws_picking_rate = picking_rate
        self.ws_occupied = False
        self.ws_orders = orders

    def __repr__(self):
        return str(self.ws_id) + ' ' + str(self.ws_location)

    def is_free(self):
        return not self.ws_occupied

    def are_orders_in_line(self):
        return len(self.ws_orders) != 0

    def get_ind(self):
        return self.ws_id

    def get_location(self):
        return self.ws_location

    def assign_robot_to_workstation(self):
        self.ws_occupied = True
        return

    def assign_order_to_picking(self, robot_obj):
        time_till_pick_finish = -1
        if not self.are_orders_in_line():
            time_till_pick_finish = np.random.exponential(1.0/self.ws_picking_rate)
        else:
            self.ws_orders.append(robot_obj)
        return time_till_pick_finish

    def serve_order_from_line(self):
        if self.are_orders_in_line():
            curr_robot = self.ws_orders.pop(0)
            time_till_pick_finish = np.random.exponential(1.0 / self.ws_picking_rate)
            return time_till_pick_finish, curr_robot
        else:
            self.ws_occupied = False
            return None


class Item:
    """
    #### Item's class
    ##### attributes
    - item id
    - item_pod_lst - pods that contain this kind of item
    """
    def __init__(self, item_id, pod_lst=[]):
        self.item_id = item_id
        self.item_pod_lst = pod_lst

    def __repr__(self):
        return str(self.item_id) + ' ' + str(self.item_pod_lst)


class Pod:
    """
    #### Pod's class
    - pod id
    - pod x location
    - pod y location
    - pod in use - if the pod is in use by a robot or not
    """
    def __init__(self, pod_id, pod_x, pod_y, pod_in_use=0):
        self.pod_id = pod_id
        self.pod_x = pod_x
        self.pod_y = pod_y
        self.pod_in_use = pod_in_use

    def __repr__(self):
        return str(self.pod_id) + ' ' + str(self.pod_x) + ' ' + str(self.pod_y) + str(self.pod_in_use)

    def is_free(self):
        return self.pod_in_use == 0

    def assign_order_to_robot(self):
        self.pod_in_use = 1
        return

    def assign_robot_to_workstation(self, robot_obj):
        self.pod_x, self.pod_y = robot_obj.get_location()
        return

    def send_pod_to_store(self, empty_spot_loc):
        self.pod_x, self.pod_y = empty_spot_loc
        return

    def store_pod(self):
        self.pod_in_use = 0
        return


class Warehouse:
    """
    #### warehouse's class
    - rows of warehouse
    - pods list in warehouse
    - workstations
    - picking aisles
    - cross aisles
    """
    def __init__(self, number_of_types=60, pa=12, ca=11, r_amount=2):
        self.rows = []
        self.pods_list = []
        self.ws_list = []
        self.pa = pa
        self.ca = ca
        self.number_of_pods = self.pa * (self.ca + 1) * 10
        self.number_of_types = number_of_types
        self.number_of_pods_per_type = int(self.number_of_pods / self.number_of_types)
        self.item_types_list = []
        self.robot_list = []
        self.r_amount = r_amount

    def build_row(self, y_init, p):
        w = 3
        x_jumps = 1
        x_init = 0.5
        y_jumps = 0
        lst = [[x_init, y_init, 1]]
        self.pods_list.append(Pod(p, x_init, y_init))
        p += 1
        for i in range(12):
            for l in range(4):
                lst.append([lst[-1][0] + x_jumps, lst[-1][1] + y_jumps, 1])
                self.pods_list.append(Pod(p, lst[-1][0], lst[-1][1]))
                p += 1
            lst.append([lst[-1][0] + w, lst[-1][1] + y_jumps, 1])
            self.pods_list.append(Pod(p, lst[-1][0], lst[-1][1]))
            p += 1
        self.pods_list = self.pods_list[:-1]
        return lst[:-1], p - 1

    def build_warehouse(self):
        y_init = 2.5
        p = 0
        for i in range(24):
            new, p = self.build_row(y_init, p)
            self.rows.append(new)
            if i % 2 == 0:
                y_init += 3
            else:
                y_init += 1
        self.build_ws()
        self.build_pods_per_items()
        self.create_robots()

    def build_ws(self):
        self.ws_list.append(WorkStation(6.0, 0, 0))
        self.ws_list.append(WorkStation(41.0, 0, 1))
        self.ws_list.append(WorkStation(76.0, 0, 2))

    def build_pods_per_items(self):
        nums = np.random.choice(self.number_of_pods, self.number_of_pods, replace=False)
        for i in range(self.number_of_types):
            self.item_types_list.append(
                Item(i, nums[self.number_of_pods_per_type * i:self.number_of_pods_per_type * (i + 1)]))

    def create_robots(self):
        for r in range(self.r_amount):
            self.robot_list.append(Robot(0, 0, r))

    # def find_xy(self, x, y):
    #     for row in range(24):
    #         for col in range(60):
    #             if [x, y, 1] == self.rows[row][col]:
    #                 return row, col

    def find_by_xy(self, x, y):
        for row in range(24):
            for col in range(60):
                if [x, y, 1] == self.rows[row][col]:
                    return row, col

    def find_by_arr(self, row, col):
        return self.rows[row][col]

    def update_empty_warehouse(self, row, col):
        self.rows[row][col][2] = 0

    def update_not_empty_warehouse(self, row, col):
        self.rows[row][col][2] = 1

    def find_pod_by_ind(self, pod_ind):
        return self.pods_list[pod_ind]

    def find_ws_by_ind(self, ws_ind):
        return self.ws_list[ws_ind]

    def find_available_robots(self):
        available_robots = []
        for robot in self.robot_list:
            if robot.is_free():
                available_robots.append(robot)
        return available_robots

    def find_available_pods(self, item_type):
        # check the location of the pods contain this item type
        curr_item_pods_list = self.item_types_list[item_type].item_pod_lst
        available_pods = []
        for pod_ind in curr_item_pods_list:
            pod = self.pods_list[pod_ind]
            if pod.is_free():
                available_pods.append(pod)
        return available_pods

    def find_available_workstations(self):
        available_ws = []
        for station in self.ws_list:
            if station.is_free():
                available_ws.append(station)
        return available_ws

    def release_pod_spot(self, loc):
        ws_row, ws_col = self.find_by_xy(loc[0], loc[1])
        self.update_empty_warehouse(ws_row, ws_col)
        return ws_row, ws_col

    def keep_empty_spot(self, row, col):
        spot_x, spot_y, occupancy = self.find_by_arr(row, col)
        self.update_not_empty_warehouse(row, col)
        return spot_x, spot_y
