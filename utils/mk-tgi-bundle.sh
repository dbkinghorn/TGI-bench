#!/usr/bin/env bash

# This script will create a fresh enroot bundle for the HF TGI server

# Exit on errors
set -e

# Check to see if enroot is installed
if ! command -v enroot &>/dev/null; then
  echo "You need enroot installed to run this script"
  exit
fi

# Set TGI version
# https://github.com/huggingface/text-generation-inference/tree/main

TGI_VERSION=1.0.3
LOCAL_DIR=~/.local/share/enroot

# Create enroot container
if [ ! -f huggingface+text-generation-inference+$TGI_VERSION.sqsh ]; then
  enroot import docker://ghcr.io#huggingface/text-generation-inference:$TGI_VERSION
fi

enroot create --force --name tgi-$TGI_VERSION huggingface+text-generation-inference+$TGI_VERSION.sqsh

# Edit /etc/rc inside the local enroot container files
# Make the container start $@ or bash instead of text-generation-launcher
# We will pass the command to run tgi when we start it
sed -i 's|exec '\''text-generation-launcher'\'' "$@"|exec "$@"|g' $LOCAL_DIR/tgi-$TGI_VERSION/etc/rc
sed -i "s|exec 'text-generation-launcher' '--json-output'|exec '/bin/bash'|g" $LOCAL_DIR/tgi-$TGI_VERSION/etc/rc

# Write script to install nvidia container toolkit to /root/install-nvidia-container-toolkit.sh
cat <<EOF >$LOCAL_DIR/tgi-$TGI_VERSION/root/install-nvidia-container-toolkit.sh
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
chmod +x $LOCAL_DIR/tgi-$TGI_VERSION/root/install-nvidia-container-toolkit.sh

# Start the container and run the script
enroot start --rw --root tgi-$TGI_VERSION /root/install-nvidia-container-toolkit.sh
# Remove the script
rm $LOCAL_DIR/tgi-$TGI_VERSION/root/install-nvidia-container-toolkit.sh

# Now export the container and create a new bundle
enroot export tgi-$TGI_VERSION
enroot bundle -a tgi-$TGI_VERSION.sqsh
