# Metriks Data Producer

Data producer uses ebpf kernel probing and prints network data to console or sends data to Kafka for consumption
 
## Installation (Default)

    - Prerequisites 
    
        Install and run Kafka and Zookeeper containers (See /kafka/Readme.md)

    - Build the Metriks Data Producer Docker Image
        
        Go to the /bpf subfolder

        Build the data processor Docker image

            % docker build -t producer-image-mtk .

    - Install and run the Metriks Data Producer

        Start a data producer Docker container
            % docker run -it --rm --privileged -v /lib/modules:/lib/modules:ro -v /etc/localtime:/etc/localtime:ro --pid=host --name producer-mtk --link kafka-container producer-image-mtk 

        Run the data producer python script
            % ./dp.sh
            or 
            % python3 data_producer.py

        Alternatively, to run in Console mode/no kafka
            % python3 console_display.py    

    - Troubleshooting from Metriks Data processor-mtk container:
        Make sure kafka-continer:9092 is found 
        # wget -O- kafka-container:9092

## Option 2: Console mode, no Kafka

    - Prerequisites (none)

        SKIP Kafka and Zookeeper install steps

    - Build the event-handling-only data processor Docker image (no data will be sent to Kafka)

        % docker build -t producer-image-mtk -f DockerfileEH .

    - Install and run the Metriks Data Processor.

        Same Install and run steps as above  

            
              