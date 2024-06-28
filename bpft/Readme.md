
## BPFTrace files for tracking network metrics
     httpcodes.bt - looks for http 200, 404, and 500 return codes


## Building and Running the Docker Container
To build and run the Docker container using this Dockerfile:

Build the Docker Image:

    docker build -t ebpf-http-metrics .

Run the Docker Container:

    docker run -d -p 8000:8000 --privileged --name /
    ebpf-http-metrics-container ebpf-http-metrics

-d: Runs the container in detached mode.
-p 8000:8000: Maps port 8000 from the container to port 8000 on the host (for accessing Prometheus metrics).
--privileged: Allows the container to run with extended privileges needed for eBPF operations.
--name ebpf-http-metrics-container: Assigns a name to the running container for easier management.


## Access Prometheus Metrics:

Open your web browser and navigate to http://localhost:8000/metrics to view the Prometheus metrics served by the container.

Notes:
Ensure your Docker host supports eBPF operations and has appropriate permissions (--privileged flag may be required).

Adjust the httpcodes.bt and http_metrics.py scripts as per your specific metrics requirements.

Use Grafana or other visualization tools to create dashboards and monitor the captured metrics effectively.

The Dockerfile provides a straightforward way to encapsulate your eBPF monitoring setup within a containerized environment, making it easier to deploy and manage across different platforms.




