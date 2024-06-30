#include <uapi/linux/ptrace.h>
#include <net/sock.h>

BPF_PERF_OUTPUT(tcp_events);

int trace_tcp_connect(struct pt_regs *ctx, struct sock *sk) {
    u32 pid = bpf_get_current_pid_tgid();

    // Retrieve source and destination IP addresses and ports
    struct {
        u32 pid;
        u32 saddr;
        u32 daddr;
        u16 sport;
        u16 dport;
    } data = {
        .pid = pid,
        .saddr = sk->__sk_common.skc_rcv_saddr,
        .daddr = sk->__sk_common.skc_daddr,
        .sport = sk->__sk_common.skc_num,
        .dport = sk->__sk_common.skc_dport,
    };

    // Output to user space
    tcp_events.perf_submit(ctx, &data, sizeof(data));

    return 0;
}
