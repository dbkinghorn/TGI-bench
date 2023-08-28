#!/usr/bin/env bash

# Shows currect state for NVIDIA GPUs
# index  name  persistence-mode  temperature  gpu-utisization mem-utilization powerlimit-default power-limit

# loop value
t=${1:-3}
nvidia-smi --query-gpu=index,gpu_name,utilization.gpu,utilization.memory,power.draw,temperature.gpu,fan.speed,clocks_throttle_reasons.sw_thermal_slowdown,clocks.current.graphics,clocks.current.memory --format=csv -l $t
