# FROM docker/for-desktop-kernel:5.10.25-6594e668feec68f102a58011bb42bd5dc07a7a9b AS ksrc
FROM docker/for-desktop-kernel:5.15.49-pr-865cda400dbf95b8b90be9bbfdceef3bcffe1e2c as ksrc
FROM ubuntu:latest

WORKDIR /
COPY --from=ksrc /kernel-dev.tar /
RUN tar xf kernel-dev.tar && rm kernel-dev.tar


RUN apt-get update && apt-get install -y linux-headers-generic build-essential

RUN apt install -y kmod python3-bpfcc

COPY hello_world.py /root

WORKDIR /root
CMD mount -t debugfs debugfs /sys/kernel/debug && /bin/bash