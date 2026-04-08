import random

class TrafficEnv:
    def __init__(self, config=None):
        if config is None:
            config = {}
            
        arr_rate = config.get("arrival_rate", 0.3)
        if isinstance(arr_rate, list):
            self.num_lanes = len(arr_rate)
        else:
            self.num_lanes = 2 if config.get("max_cars_per_lane") == 5 else 4
            
        self.max_cars_per_lane = config.get("max_cars_per_lane", 10)
        
        if isinstance(arr_rate, list):
            self.arrival_rate = arr_rate
        else:
            self.arrival_rate = [arr_rate] * self.num_lanes
            
        self.no_emergency = config.get("no_emergency", False)
        self.emergency_prob = config.get("emergency_prob", 0.0)
        self.max_steps = config.get("max_steps", 100)
        
        self.lanes = ["N", "S", "E", "W"][:self.num_lanes]
        self.seed = config.get("random_seed", 42)
        self.rng = random.Random(self.seed)
        
        self.reset()
        
    def reset(self):
        self.steps = 0
        self.cars_per_lane = [0] * self.num_lanes
        self.total_wait_time = [0.0] * self.num_lanes
        self.red_time_per_lane = [0] * self.num_lanes
        self.current_signal = "NS"
        self.signal_timer = 0
        self.emergency_present = False
        self.emergency_lane = None
        self.emergency_wait = 0
        
        self.all_cars_wait_times = []
        self.total_cars_arrived = 0
        self.total_cars_cleared = 0
        self.total_emergencies_arrived = 0
        self.emergencies_cleared_under_5 = 0
        self.emergency_waited_over_10 = False
        self.starvation_occurred = False
        
        return self.state()
        
    def _get_avg_wait_times(self):
        avg_waits = []
        for i in range(self.num_lanes):
            if self.cars_per_lane[i] > 0:
                avg_waits.append(self.total_wait_time[i] / self.cars_per_lane[i])
            else:
                avg_waits.append(0.0)
        return avg_waits
        
    def state(self):
        return {
            "cars_per_lane": list(self.cars_per_lane),
            "wait_time_per_lane": self._get_avg_wait_times(),
            "current_signal": self.current_signal,
            "signal_timer": self.signal_timer,
            "emergency_present": self.emergency_present,
            "emergency_lane": self.emergency_lane
        }
        
    def step(self, action):
        positive_reward = 0.0
        negative_reward = 0.0
        
        self.steps += 1
        self.signal_timer += 1
        
        # 1. Apply action
        if action == 1:
            self.current_signal = "EW" if self.current_signal == "NS" else "NS"
            self.signal_timer = 0
        elif action == 2:
            if self.emergency_present and self.emergency_lane is not None:
                if self.emergency_lane in ["N", "S"]:
                    self.current_signal = "NS"
                else:
                    self.current_signal = "EW"
                self.signal_timer = 0
            else:
                # Spec: if no emergency exists, override behaves as a normal switch.
                self.current_signal = "EW" if self.current_signal == "NS" else "NS"
                self.signal_timer = 0
                
        # 2. Move vehicles
        if self.num_lanes == 2:
            # In 2-lane mode (N/S only), both lanes are always the active phase.
            green_lanes = [0, 1]
        else:
            green_lanes = [0, 1] if self.current_signal == "NS" else [2, 3]
            
        prev_avg_wait = sum(self._get_avg_wait_times()) / self.num_lanes if self.num_lanes > 0 else 0
        prev_max_queue = max(self.cars_per_lane) if self.cars_per_lane else 0
        prev_min_queue = min(self.cars_per_lane) if self.cars_per_lane else 0
        
        cars_cleared = 0
        emergency_cleared = False
        
        for i in range(self.num_lanes):
            self.total_wait_time[i] += self.cars_per_lane[i]
            
            lane_name = self.lanes[i]
            if i in green_lanes:
                self.red_time_per_lane[i] = 0
                cleared = min(3, self.cars_per_lane[i])
                
                if cleared > 0:
                    avg_wait_for_cleared = self.total_wait_time[i] / self.cars_per_lane[i]
                    self.total_wait_time[i] = max(0.0, self.total_wait_time[i] - avg_wait_for_cleared * cleared)
                    self.all_cars_wait_times.extend([avg_wait_for_cleared] * cleared)
                    
                self.cars_per_lane[i] -= cleared
                cars_cleared += cleared
                self.total_cars_cleared += cleared
                
                if self.emergency_present and self.emergency_lane == lane_name:
                    emergency_cleared = True
                    if self.emergency_wait <= 5:
                        self.emergencies_cleared_under_5 += 1
                    self.emergency_present = False
                    self.emergency_lane = None
                    self.emergency_wait = 0
            else:
                self.red_time_per_lane[i] += 1
                if self.red_time_per_lane[i] > 15:
                    self.starvation_occurred = True
                    if self.red_time_per_lane[i] > 10:
                        negative_reward -= 1.0 # starvation penalty
                        
        positive_reward += cars_cleared * 0.5
        if emergency_cleared:
            positive_reward += 2.0
            
        current_avg_wait = sum(self._get_avg_wait_times()) / self.num_lanes if self.num_lanes > 0 else 0
        if current_avg_wait < prev_avg_wait:
            positive_reward += 0.3
            
        current_max_queue = max(self.cars_per_lane) if self.cars_per_lane else 0
        current_min_queue = min(self.cars_per_lane) if self.cars_per_lane else 0
        if (current_max_queue - current_min_queue) < (prev_max_queue - prev_min_queue):
            positive_reward += 0.1
            
        # 3. Add new cars
        for i in range(self.num_lanes):
            if self.rng.random() < self.arrival_rate[i]:
                if self.cars_per_lane[i] < self.max_cars_per_lane:
                    self.cars_per_lane[i] += 1
                    self.total_cars_arrived += 1
                    
        # 4. Check for emergency vehicle
        if not self.no_emergency and not self.emergency_present:
            if self.rng.random() < self.emergency_prob:
                self.emergency_present = True
                self.emergency_lane = self.rng.choice(self.lanes)
                self.emergency_wait = 0
                self.total_emergencies_arrived += 1
        elif self.emergency_present:
            self.emergency_wait += 1
            if self.emergency_wait > 5 and action != 2:
                negative_reward -= 3.0
            if self.emergency_wait > 10:
                self.emergency_waited_over_10 = True
                
        # 5. Compute negative rewards scaling
        avg_wait_times = self._get_avg_wait_times()
        for i in range(self.num_lanes):
            if self.cars_per_lane[i] > 0:
                negative_reward -= 0.2 * self.cars_per_lane[i] * (1.0 + avg_wait_times[i] / 10.0)
                
        total_reward = positive_reward + negative_reward
        
        # 6. Check done
        done = self.steps >= self.max_steps
        if sum(self.cars_per_lane) == 0:
             done = True
        
        info = {
            "all_cars_wait_times": self.all_cars_wait_times,
            "total_cars_arrived": self.total_cars_arrived,
            "total_cars_cleared": self.total_cars_cleared,
            "total_emergencies_arrived": self.total_emergencies_arrived,
            "emergencies_cleared_under_5": self.emergencies_cleared_under_5,
            "emergency_waited_over_10": self.emergency_waited_over_10,
            "starvation_occurred": self.starvation_occurred
        }
        
        return self.state(), total_reward, done, info
