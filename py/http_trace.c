#include <linux/ptrace.h>
#include <linux/skbuff.h>
#include <linux/sched.h>


BPF_PERF_OUTPUT(http_events);

int trace_http_request(struct pt_regs *ctx, struct sock *sk, struct sk_buff *skb) {
    u32 pid = bpf_get_current_pid_tgid();
    u64 msg_len = skb->len;

    // Filter HTTP traffic (adjust as needed)
    if (msg_len > 0) {
        // Prepare data to send to user space
        struct {
            u32 pid;
            u64 msg_len;
        } data = {
            .pid = pid,
            .msg_len = msg_len,
        };

        // Output to user space
        http_events.perf_submit(ctx, &data, sizeof(data));
    }

    return 0;
}
