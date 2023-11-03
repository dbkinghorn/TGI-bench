#!/usr/bin/env bash

# This script is used to run the benchmarks for the TGI paper.

# enable job control
set -m

# Set the HF token
. .env

# Move old log files out of the way
[ -f tgi.log ] && mv tgi.log tgi.log.old
[ -f gpu.log ] && mv gpu.log gpu.log.old
[ -f results.csv ] && mv results.csv results.csv.old
[ -f summary.out ] && mv summary.out summary.out.old
[ -f summary1d.out ] && mv summary.out summary1d.out.old

MODEL="meta-llama/Llama-2-70b-chat-hf"
REVISION="08751db2aca9bf2f7f80d2e516117a53d7450235"
SHARDS=4
HOST=127.0.0.1
PORT=8088
TGI_VERSION=1.0.3
TGIL=text-generation-launcher

./tgi-${TGI_VERSION}.run --rw --root --env HUGGING_FACE_HUB_TOKEN --mount .:/data -- $TGIL --model-id $MODEL --revision $REVISION --num-shard $SHARDS --port $PORT --hostname $HOST --json-output >tgi.log &

# Wait for the server to start
monitor_file() {
    filename=$1
    text=$2

    # Wait for container bundle to be extracted
    while [ ! -s $filename ]; do
        sleep 10
    done

    tgi_launcher_pid=$(pgrep -f --newest text-generation-launcher)

    while :; do
        if grep -q "$text" $filename; then
            echo "TGI Server running"
            break
        else
            echo "Waiting for TGI Server to start"
            sleep 10
        fi
    done
}

monitor_file "tgi.log" "Connected"

# Get the number of prompt runs from the command line
if [ $# -gt 0 ]; then
    NUM_RUNS=$1
else
    NUM_RUNS=5
fi

# Start the GPU performance monitoring
nvidia-smi --query-gpu=index,gpu_name,utilization.gpu,utilization.memory,power.draw,temperature.gpu,fan.speed,clocks_throttle_reasons.sw_thermal_slowdown,clocks.current.graphics,clocks.current.memory --format=csv -l 1 >gpu.log &

nvidia_smi_pid=$!

./bench-client.py $NUM_RUNS
kill $nvidia_smi_pid
./extract-log-data.py tgi.log
# Stopping the launcher will stop the container
kill $tgi_launcher_pid
