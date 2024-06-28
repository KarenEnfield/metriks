from bcc import BPF
import time

# Define the eBPF program
bpf_program = """
BPF_HASH(start, u32, u64);

int trace_http_request(struct pt_regs *ctx) {
    u32 pid = bpf_get_current_pid_tgid();
    u64 ts = bpf_ktime_get_ns();
    start.update(&pid, &ts);
    return 0;
}

int trace_http_response(struct pt_regs *ctx) {
    u32 pid = bpf_get_current_pid_tgid();
    u64 *tsp, delta;

    tsp = start.lookup(&pid);
    if (tsp != 0) {
        delta = bpf_ktime_get_ns() - *tsp;
        bpf_trace_printk("HTTP Latency (pid %d): %lld ns\\n", pid, delta);
        start.delete(&pid);
    }
    return 0;
}
"""

# Load the eBPF program
b = BPF(text=bpf_program)
b.attach_tracepoint(tp="syscalls/sys_enter_execve", fn_name="trace_http_request")
b.attach_tracepoint(tp="syscalls/sys_exit_execve", fn_name="trace_http_response")

# Read and print traced data
while True:
    try:
        (task, pid, cpu, flags, ts, msg) = b.trace_fields()
        print(msg)
    except KeyboardInterrupt:
        exit()
