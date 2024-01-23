# MetriKs Visualizer

## Build the Visualizer image
    From the /visualize directory type:
        docker build -t visualizer-image-mtk .

## Install and run the Visualizer container
    docker run -it \
        --privileged \
        -v /lib/modules:/lib/modules:ro \
        -v /etc/localtime:/etc/localtime:ro \
        --pid=host \
        --name visualizer-mtk \
        --link kafka-container \
        visualizer-image-mt