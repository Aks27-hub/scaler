from traffic_env import TrafficEnv
from easy_task import EasyTask, grade_easy
import json

def test_easy_env_bug():
    task = EasyTask()
    config = task.get_config()
    env = TrafficEnv(config)
    env.reset()
    
    print(f"Initial state: {env.state()}")
    
    # In easy task, num_lanes = 2.
    # Initial signal is "NS". Lanes 0 and 1 should be green.
    # Let's switch to "EW".
    state, reward, done, info = env.step(1) # Action 1 is switch
    print(f"State after switch: {state}")
    
    # In 2-lane mode, "EW" should probably mean something else or be ignored, 
    # but currently it makes green_lanes = []
    
    # Let's check if cars clear in "EW" mode
    env.cars_per_lane = [5, 5]
    state, reward, done, info = env.step(0) # Hold "EW"
    print(f"Lanes after step in EW mode: {state['cars_per_lane']}")
    if state['cars_per_lane'] == [5, 5]:
        print("BUG CONFIRMED: No cars cleared in EW mode for 2-lane intersection.")
    else:
        print("No bug or different behavior.")

if __name__ == "__main__":
    test_easy_env_bug()
