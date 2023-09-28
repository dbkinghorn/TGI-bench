#!./mm/envs/py-client-env/bin/python

import sys
import csv
import json
import pandas as pd


def extract_info(line):
    if line:
        line = dict(json.loads(line))
        timestamp = line["timestamp"]
        validation_time = (
            pd.to_timedelta(line["span"]["validation_time"]).total_seconds() * 1000
        )
        queue_time = pd.to_timedelta(line["span"]["queue_time"]).total_seconds() * 1000
        inference_time = (
            pd.to_timedelta(line["span"]["inference_time"]).total_seconds() * 1
        )
        time_per_token = (
            pd.to_timedelta(line["span"]["time_per_token"]).total_seconds() * 1000
        )
        return timestamp, validation_time, queue_time, inference_time, time_per_token
    else:
        return None


if len(sys.argv) < 2:
    print("Please provide the name of the log file as a command line argument.")
    sys.exit()

log_file_name = sys.argv[1]
output_file_name = "results.csv"

with open(log_file_name, "r") as f, open(output_file_name, "w", newline="") as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow(
        [
            "Timestamp",
            "Validation Time (ms)",
            "Queue Time (ms)",
            "Inference Time (s)",
            "Time per Token (ms)",
        ]
    )
    for line in f:
        if "HTTP request" in line:
            info = extract_info(line)
            if info:
                writer.writerow(info)

df = pd.read_csv(output_file_name)

summary = df.describe(percentiles=[])

print(summary)

with open("summary.out", "a") as f:
    f.write(summary.to_string())
    f.write('\n')
