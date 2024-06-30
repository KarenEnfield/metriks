#include <uapi/linux/ptrace.h>
#include <net/sock.h>

BPF_PERF_OUTPUT(dns_events);

int trace_dns_query(struct pt_regs *ctx, struct sock *sk) {
    u32 pid = bpf_get_current_pid_tgid();

    // Retrieve source and destination IP addresses and ports
    struct {
        u32 pid;
        char query_domain[256]; // Adjust size as needed
        u64 response_time_ns;
    } data = {
        .pid = pid,
    };

    // Capture query domain and calculate response time (example)
    bpf_probe_read_str(data.query_domain, sizeof(data.query_domain), sk->__sk_common.skc_daddr);
    data.response_time_ns = bpf_ktime_get_ns();

    // Output to user space
    dns_events.perf_submit(ctx, &data, sizeof(data));

    return 0;
}
