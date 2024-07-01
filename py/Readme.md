## Metrics Collector
# Building and Running the Docker Container

# 1. Build the Docker Image:

    % docker build -t ebpf-kafka-collector .

# 2. Run the Docker Container:

    % docker run --rm -it \
        --privileged \
        --mount type=bind,source=/sys/fs/bpf,target=/sys/fs/bpf \
        -v /etc/localtime:/etc/localtime:ro \
        --pid=host \
        --name metrics-collector-mtk \
        --link kafka-container \
        ebpf-kafka-collector


# Note: The --privileged flag is necessary for running eBPF programs as they require higher privileges to access kernel features.

# Run these commands to point the kernel to the compatible docker jammy headers
mkdir /lib/modules/6.6.31-linuxkit/
chmod 777 /lib/modules/5.15.0-113-generic
ln -s /lib/modules/5.15.0-113-generic/build /lib/modules/6.6.31-linuxkit/build
python3 metrics_collector.py