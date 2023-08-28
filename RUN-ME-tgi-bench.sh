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

MODEL="meta-llama/Llama-2-70b-chat-hf"
SHARDS=4
HOST=127.0.0.1
PORT=8088

./tgi-1.0.1-2.run --rw --root --env HUGGING_FACE_HUB_TOKEN --mount .:/data --  --model-id $MODEL --num-shard $SHARDS --port $PORT --hostname $HOST --trust-remote-code --json-output > tgi.log &

sleep 30

# Get the number of runs from the command line
if [ $# -gt 0 ]; then
    NUM_RUNS=$1
else
    NUM_RUNS=5
fi

./bench-client.py $NUM_RUNS 
./extract-log-data.py tgi.log

killall text-generation-launcher
