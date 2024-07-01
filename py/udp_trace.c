#include <linux/ptrace.h>
#include <linux/skbuff.h>
#include <linux/ip.h>

struct tcphdr {
    __be16 source;
    __be16 dest;
    __be32 seq;
    __be32 ack_seq;
    union {
        struct {
            __u16 res1:4;
            __u16 doff:4;
            __u16 fin:1;
            __u16 syn:1;
            __u16 rst:1;
            __u16 psh:1;
            __u16 ack:1;
            __u16 urg:1;
            __u16 ece:1;
            __u16 cwr:1;
        };
        __u16 flags;
    };
    __be16 window;
    __sum16 check;
    __be16 urg_ptr;
};

BPF_PERF_OUTPUT(udp_events);

int trace_udp_sendmsg(struct pt_regs *ctx, struct sock *sk,  struct sk_buff *skb) {
    u32 pid = bpf_get_current_pid_tgid();
    struct tcphdr *tcph = (struct tcphdr *)(skb->data + skb->transport_header);
    struct iphdr *iph = (struct iphdr *)(skb->data + skb->network_header);

    // Retrieve source and destination IP addresses and ports
    struct {
        u32 pid;
        u32 saddr;
        u32 daddr;
        u16 sport;
        u16 dport;
    } data = {
        .pid = pid,
        .saddr = iph->saddr,
        .daddr = iph->daddr,
        .sport = bpf_ntohs(tcph->source),
        .dport = bpf_ntohs(tcph->dest),
    };

    // Output to user space
    udp_events.perf_submit(ctx, &data, sizeof(data));

    return 0;
}
