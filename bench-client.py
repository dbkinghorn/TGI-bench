#!./mm/envs/py-client-env/bin/python
# run it from our local python environment

from text_generation import Client
import time
import os
import sys

# Wait for the server to start
filename = "tgi.log"
text = "Connected"


def monitor_file(filename, text):
    while not os.path.exists(filename):
        time.sleep(10)

    while True:
        with open(filename, "r") as file:
            if text in file.read():
                print(f"TGI Server running")
                break
        print(f"Waiting for TGI Server to start")
        time.sleep(10)


monitor_file(filename, text)

# Start the GPU performance monitoring
os.system(
    "nvidia-smi --query-gpu=index,gpu_name,utilization.gpu,utilization.memory,power.draw,temperature.gpu,fan.speed,clocks_throttle_reasons.sw_thermal_slowdown,clocks.current.graphics,clocks.current.memory --format=csv -l 1 > gpu.log &"
)

client = Client("http://127.0.0.1:8088", timeout=40)


prompt = f"""
<s>[INST] <<SYS>>
You are a helpful, respectful and honest assistant. Always answer as helpfully as possible, while being safe.  Your answers should not include any harmful, unethical, racist, sexist, toxic, dangerous, or illegal content. Please ensure that your responses are socially unbiased and positive in nature.

If a question does not make any sense, or is not factually coherent, explain why instead of answering something not correct. If you don't know the answer to a question, please don't share false information. Instead, say that you don't know the answer.
<</SYS>>

Who is Robert Oppenheimer? [/INST]

"""

# time the inference


def get_inference_time(prompt):
    start = time.time()
    client.generate(
        f"{prompt}", temperature=0.95, top_k=1, top_p=0.9, max_new_tokens=500
    )
    end = time.time()
    return end - start


# Set the number of runs
if len(sys.argv) > 1:
    num_runs = sys.argv[1]
else:
    num_runs = 3

for n in range(int(num_runs)):
    print(f"Time taken: {get_inference_time(prompt)} seconds")

# Stop the GPU performance monitoring
os.system("killall nvidia-smi")