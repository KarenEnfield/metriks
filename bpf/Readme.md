# Metriks Data Processor

Data processor monitors TCP activity, and informs userspace and Kafka of event data 
 
## Installation (Default)

    - Prerequisites 
    
        Install and run Kafka and Zookeeper containers on Docker (See /kafka/Readme.md)

    - Build the data processor Docker Image
        
        Go to the /bpf subfolder

        Build the data processor Docker image

            % docker build -t data-processor -f Dockerfile .

    - Install and run the Metriks Data Processor

        Start a data processor Docker container
            % docker run -it --rm --privileged -v /lib/modules:/lib/modules:ro -v /etc/localtime:/etc/localtime:ro --pid=host --name procesor-container data-processor

        Run the data processor python script
            % ./dp.sh
            or 
            % python3 data-processor.py


## Option 2: Data to Userspace only, no Kafka

    - Prerequisites (none)

        SKIP Kafka and Zookeeper install steps

    - Build the event-handling-only data processor Docker image (no data will be sent to Kafka)

        % docker build -t data-processor -f DockerfileEH .

    - Install and run the Metriks Data Processor.

        Same Install and run steps as above  
              