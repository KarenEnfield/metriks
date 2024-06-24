
# Use an official Python runtime as a parent image
#FROM python:3.11
FROM ubuntu:latest

# Set the working directory
WORKDIR /app

ARG DEBIAN_FRONTEND=noninteractive
ENV TZ=US
ENV DISPLAY=host.docker.internal:0

# Set the MPLBACKEND environment variable to Agg
# ENV MPLBACKEND TkAgg

RUN apt-get update && apt-get install -y \
    python3-full \
    python3-pip \
    python3-tk \
    git \
    catimg 

RUN python3 -m venv myenv
# RUN source myenv/bin/activate
RUN myenv/bin/pip3 install git+https://github.com/dpkp/kafka-python.git
#RUN myenv/bin/pip3 install kafka-python
RUN myenv/bin/pip3 install networkx 
RUN myenv/bin/pip3 install matplotlib 
RUN myenv/bin/pip3 install pytz 


# Copy Python scripts
# epbf data processing of tcp events logged to userspace, event data sent to kafka
COPY tcp_connections_visualizer.py /app/visualize.py
COPY config.ini /app/config.ini
COPY run.sh /app/run.sh
RUN chmod +x /app/run.sh
COPY commit.sh /app/commit.sh
RUN chmod +x /app/commit.sh


# Cant save the image if it automatically closes!
# CMD ["python3", "visualize.py"]


