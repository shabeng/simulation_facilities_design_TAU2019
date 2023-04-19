import matplotlib.pyplot as plt
import numpy as np

from simulation import Simulation


def run_experiment_1(time_limit=2*604800, repeat=1, save_path='graphs'):
    """Experiment 1 - estimates the maximum throughput of the system for different number of robots"""
    # Params
    robot_nums = [2, 4, 10]
    entering_rates = [0.025, 0.035, 0.08]
    exp_res = []
    for r in range(len(robot_nums)):
        res = []
        robot_num = robot_nums[r]
        entering_rate = entering_rates[r]
        print(f'Starting {robot_num}...')
        for s in range(repeat):
            simu_instance = Simulation(time_limit=time_limit, robot_num=robot_num, order_enter_rate=entering_rate)
            simu_instance.run_simulation()
            res.append(len(simu_instance.served_orders[simu_instance.served_orders_while_warmup:]))
        exp_res.append((robot_num, np.mean(res)))

    for res in exp_res:
        before_exploding_rate = res[1] / (time_limit*(1-simu_instance.warmup_dur))
        robot_num = res[0]
        epsilon = 0.001
        print(f'Starting {robot_num}...')
        simu_instance_exp = Simulation(time_limit=time_limit, robot_num=robot_num,
                                       order_enter_rate=before_exploding_rate + epsilon)
        simu_instance_exp.run_simulation()
        plt.plot(simu_instance_exp.times_lst, simu_instance_exp.order_cnt_lst,
                 label=f'{np.round(before_exploding_rate, 3)} + epsilon')

        simu_instance_no_exp = Simulation(time_limit=time_limit, robot_num=robot_num,
                                          order_enter_rate=before_exploding_rate - epsilon)
        simu_instance_no_exp.run_simulation()
        plt.plot(simu_instance_no_exp.times_lst, simu_instance_no_exp.order_cnt_lst,
                 label=f'{np.round(before_exploding_rate, 3)} - epsilon')
        plt.xlabel('Time')
        plt.ylabel('Number of Orders in the Warehouse')
        plt.title(f'Entering Rates Before and After Explosion for {robot_num} Robots')
        plt.legend()
        plt.savefig(f'{save_path}/experiment1_num_robots_{robot_num}.png')
        plt.show()
    return exp_res


def run_experiment_2(time_limit=2*604800, repeat=1, save_path='graphs'):
    """Experiment 2 - estimates the service time of orders for different number of robots and enter rate"""
    # Params
    rates = [200.0 / (60*60), 500.0 / (60*60)]
    robot_ranges = [(1, 20), (15, 35)]
    exp_results = []
    for i in range(len(rates)):
        enter_rate = rates[i]
        min_robot, max_robot = robot_ranges[i]
        avg_lst = []
        r_num_lst = []
        service_times = []
        std_times = []
        for robot_num in range(min_robot, max_robot + 1):
            print(f'enter rate = {enter_rate} | robot num = {robot_num} | Starting... ')
            n_repeat = 0
            for s in range(repeat):
                n = 0
                cum_sum = 0
                simu_instance = Simulation(time_limit=time_limit, robot_num=robot_num, order_enter_rate=enter_rate)
                simu_instance.run_simulation()

                for order in simu_instance.served_orders[simu_instance.served_orders_while_warmup:]:
                    service_time = order.o_exit_time - order.o_enter_time
                    n += 1
                    cum_sum += service_time
                    service_times.append(service_time)
                n_repeat += cum_sum / n

            std_times.append(np.std(service_times))
            avg_lst.append(n_repeat/repeat)
            r_num_lst.append(robot_num)

        plt.scatter(r_num_lst, avg_lst, c='blue', label='Average')
        for k in range(len(avg_lst)):
            if k % 2 == 1:
                continue
            plt.annotate(str(np.round(avg_lst[k])), xy=(r_num_lst[k], avg_lst[k] + 10000))
        # plt.plot(r_num_lst, np.array(avg_lst) + np.array(std_times), c='red', label='+SD')
        # plt.plot(r_num_lst, np.array(avg_lst) - np.array(std_times), c='red', label='-SD')
        plt.ylabel('Service Time')
        plt.xlabel('Number of Robots')
        plt.legend()
        dur = time_limit / 60 / 60 / 24
        enter_rate_hour = np.round(enter_rate * 60 * 60)
        plt.title(f'Experiment 2 - {dur} Days with Entering Rate of {enter_rate_hour} Orders per Hour')
        plt.savefig(f'{save_path}/experiment2_{dur}_days_enterrate_{enter_rate_hour}.png')
        plt.show()
        exp_results.append((avg_lst, r_num_lst, std_times))
    return exp_results


if __name__ == '__main__':
    exp1_results = run_experiment_1(repeat=5)
    exp2_results = run_experiment_2(repeat=1)

