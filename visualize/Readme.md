# MetriKs Visualizer

Build the visualizer image
    % docker build -t visualizer-image-mtk .

Install and run the container
    % docker run -it --rm --privileged -v /lib/modules:/lib/modules:ro -v /etc/localtime:/etc/localtime:ro --pid=host --name visualizer-mtk --link kafka-container visualizer-image-mtk