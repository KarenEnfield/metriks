#!/bin/bash

# Mount debugfs
mount -t debugfs debugfs /sys/kernel/debug

# ./run.sh -v EVENTS_HTTP_ONLY -val False -v ANOTHER_VARIABLE -val some_value

# Declare an associative array to store environment variable key-value pairs
declare -A env_vars

# Parse command-line arguments
while [[ $# -gt 0 ]]; do
  key="$1"

  case $key in
    -v|--variable)
      VAR_NAME="$2"
      shift # past argument
      shift # past value
      ;;
    -val|--value)
      VAR_VALUE="$2"
      shift # past argument
      shift # past value
      ;;
    *)
      # unknown option
      shift
      ;;
  esac

  # Store key-value pair in the associative array
  env_vars["$VAR_NAME"]="$VAR_VALUE"
done

# Set the environment variables
for key in "${!env_vars[@]}"; do
  export "$key=${env_vars[$key]}"
done


# Setup environment for running the scripts and lib modules with bcc


# Find the current kernel version to create a subfolder for symbolic linking
OS_KERNEL=$(uname -r)
echo "Updated OS_KERNEL_VERSION:$OS_KERNEL"

# Get the DOCKERFILE kernel version
UBUNTU_KERNEL_VERSION=$(cat /app/docker_kernel_version.txt) 
echo "Updated UBUNTU_KERNEL_VERSION:$UBUNTU_KERNEL_VERSION"

UBUNTU_LIB_MODULES=$(find /lib/modules -name *$UBUNTU_KERNEL_VERSION*)
echo "Updated UBUNTU_LIB_MODULES:$UBUNTU_LIB_MODULES"

# Use python3 bcc, already installed
BCCPATH=$(dirname `find /usr/lib -name bcc`)
export PYTHONPATH="${PYTHONPATH:+$PYTHONPATH:}$BCCPATH"
echo "Updated PYTHONPATH:$PYTHONPATH"

# IMPORTANT SYMBOLIC OS LIB MODULE LINK TO USE THE UBUNTY JAMMY LIB MODULE FILES  
# Create a symbolic link from the expected lib module subdirectory
# to the lib module subfolder we will actually use that is compatible with Docker on Mac
mkdir /lib/modules/$OS_KERNEL
chmod 777 $UBUNTU_LIB_MODULES
ln -s $UBUNTU_LIB_MODULES/build /lib/modules/$OS_KERNEL/build

# find the bpftools for observability
TOOLSPATH=$(find /usr/lib -name linux-tools-$UBUNTU_KERNEL_VERSION*)
echo "Updated TOOLSPATH:$TOOLSPATH"
export PATH="$TOOLSPATH:$PATH"

# Monitoring tools for linux in 60 sec analysis
dpkg-reconfigure sysstat

# Run your Python script
python3 send_tcp_events.py
