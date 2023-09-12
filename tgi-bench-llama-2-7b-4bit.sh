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

MODEL="meta-llama/Llama-2-7b-chat-hf"
SHARDS=1
HOST=127.0.0.1
PORT=8088
TGI_VERSION=1.0.3
TGIL=text-generation-launcher

./tgi-${TGI_VERSION}.run --rw --root --env HUGGING_FACE_HUB_TOKEN --mount .:/data -- $TGIL --model-id $MODEL --num-shard $SHARDS --port $PORT --hostname $HOST --quantize bitsandbytes-nf4 --max-batch-prefill-tokens 2048 --json-output >tgi.log &

# Give it some time to at least start the container extraction
sleep 30

# Get the number of runs from the command line
if [ $# -gt 0 ]; then
    NUM_RUNS=$1
else
    NUM_RUNS=5
fi

./bench-client.py $NUM_RUNS
./extract-log-data.py tgi.log

killall $TGIL
