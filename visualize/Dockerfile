
# Use an official Python runtime as a parent image
# FROM python:3.10
FROM ubuntu:latest

# Set the working directory
WORKDIR /app

ARG DEBIAN_FRONTEND=noninteractive
ENV TZ=US
ENV DISPLAY=host.docker.internal:0

# Set the MPLBACKEND environment variable to Agg
# ENV MPLBACKEND TkAgg

RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-tk \
    catimg 
 
RUN pip3 install kafka-python
RUN pip3 install networkx 
RUN pip3 install matplotlib


# Copy Python scripts
# epbf data processing of tcp events logged to userspace, event data sent to kafka
COPY custom_visualization.py /app/visualize.py
COPY test.py /app/test.py
COPY plot.py /app/plot.py
COPY vz.sh /app/vz.sh
RUN chmod +x /app/vz.sh


# CMD ["python3", "visualize.py"]
