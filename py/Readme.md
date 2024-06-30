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

