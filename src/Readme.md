# MetriKs Data Producer

Data producer uses ebpf kernel probing and prints network data to console or sends data to Kafka for consumption
 
## Installation Prerequisites (Data Streaming mode) 

    Install and run Kafka and Zookeeper in Docker 
    (See Installation instructions in /kafka/Readme.md) 

## Build the MetriKs Data Producer Docker Image
        
    From directory /bpf, Type:
        docker build -t producer-image-mtk .

## Install and run the MetriKs Data Producer container

    Start a data producer Docker container

DO NOT do the recommended mounting of lib\modules:     
    docker run -it --rm --privileged \
        -v /lib/modules:/lib/modules:rw \
        -v /etc/localtime:/etc/localtime:ro \
        --pid=host \
        --name producer-mtk \
        --link kafka-container \
        producer-image-mtk

DO THIS to overwrite the lib/modules and use a docker kernel lib module instead
    docker run --rm -it \
        --privileged \
        --mount type=bind,source=/sys/fs/bpf,target=/sys/fs/bpf \
        -v /etc/localtime:/etc/localtime:ro \
        --pid=host \
        --name producer-mtk \
        --link kafka-container \
        producer-image-mtk



    Run the data producer python script
        % ./run.sh
            or type the command
        % python3 data_producer.py

        Alternatively, to run in Console mode/no kafka
            % python3 console_display.py    

    - Troubleshooting from Metriks Data processor-mtk container:
        Make sure kafka-continer:9092 is found 
        # wget -O- kafka-container:9092

## Option 2: Console mode install, no Kafka prerequisite

    - Prerequisites (none)

        You may SKIP Kafka and Zookeeper install steps

    - Build the event-handling-only data processor Docker image (no data will be sent to Kafka)

        % docker build -t producer-image-mtk -f DockerfileEH .


    - Install and run the Metriks Data Processor.

        Same Install and run steps as above 

## Option 3: Console mode/ No Kafka as Environment setting 
    
    Install with Kafka as above
    Environment variable "CONSOLE_NO_KAFKA" if defined, overrides system configuration settings
    If not explicitly set to True, it defaults to False
      

        

            
              