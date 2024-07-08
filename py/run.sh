#!/bin/bash
# Setup environment for running the scripts and lib modules with bcc
# Mount debugfs
mount -t debugfs debugfs /sys/kernel/debug

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
python3 metrics_collector.py
