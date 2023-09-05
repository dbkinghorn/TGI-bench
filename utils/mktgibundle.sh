#!/usr/bin/env bash

# This script will create a fresh enroot bundle for the HF TGI server

# Exit on errors
set -e

# Check to see if enroot is installed
if ! command -v enroot &> /dev/null
then
    echo "You need enroot installed to run this script"
    exit
fi

# Set TGI version
# https://github.com/huggingface/text-generation-inference/tree/main

TGI_VERSION=1.0.3

# Create enroot container

enroot import docker://ghcr.io#huggingface/text-generation-inference:$TGI_VERSION 
enroot create --name tgi-$TGI_VERSION huggingface+text-generation-inference+$TGI_VERSION.sqsh

# Edit /etc/rc inside the local enroot container store
sed -i "s|exec 'text-generation-launcher' '--json-output'|exec '/bin/bash'|g" ~/.local/share/enroot/tgi-$TGI_VERSION/etc/rc

# Write script to install nvidia container toolkit to /root/install-nvidia-container-toolkit.sh
cat << EOF > ~/.local/share/enroot/tgi-$TGI_VERSION/root/install-nvidia-container-toolkit.sh
#!/bin/bash
# Install nvidia container toolkit
  DIST=$(
    . /etc/os-release
    echo $ID$VERSION_ID
  )
  curl -s -L https://nvidia.github.io/libnvidia-container/gpgkey |  apt-key add -
  curl -s -L https://nvidia.github.io/libnvidia-container/$DIST/libnvidia-container.list |
     tee /etc/apt/sources.list.d/libnvidia-container.list

  apt-get update
  apt-get install --yes libnvidia-container-tools
EOF

# Make script executable
chmod +x ~/.local/share/enroot/tgi-$TGI_VERSION/root/install-nvidia-container-toolkit.sh

# Start the container and run the script
enroot start --rw --root tgi-$TGI_VERSION  /root/install-nvidia-container-toolkit.sh
 # Remove the script
rm ~/.local/share/enroot/tgi-$TGI_VERSION/root/install-nvidia-container-toolkit.sh

# Now export the container and create a new bundle
enroot export tgi-$TGI_VERSION
enroot bundle -a tgi-$TGI_VERSION.sqsh

