# metriks - eBPF for Docker Desktop on macOS

eBPF and its compiler bcc need access to some parts of the kernel and its headers to work. This image shows how you can do that with Docker Desktop for mac's linuxkit host VM.

## Prerequisites
brew install python
brew install ipython
pip3 install bcc

## Build the image

Done quite simply with:

docker build -t ebpf-for-mac .

## Run the image

It needs to run as privileged, and depending on what you want to do, having access to the host's PID namespace is pretty useful too.

docker run -it --rm \ 
  --privileged \ 
  -v /lib/modules:/lib/modules:ro \ 
  -v /etc/localtime:/etc/localtime:ro \ 
  --pid=host \ 
  ebpf-for-mac

or 
docker run -it --rm --privileged -v /lib/modules:/lib/modules:ro -v /etc/localtime:/etc/localtime:ro --pid=host ebpf-for-mac

Note: /lib/modules probably doesn't exist on your mac host, so Docker will map the volume in from the linuxkit host VM.

## Maintenance

Docker published their for-desktop kernel's on Docker hub you may need to update the Dockerfile for the latest kernel that matches your linuxkit host VM.