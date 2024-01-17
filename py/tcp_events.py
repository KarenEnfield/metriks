#!/usr/bin/env python3

from bcc import BPF

prog = """
#include <uapi/linux/ptrace.h>
#include <linux/skbuff.h>
#include <linux/ip.h>
#include <bcc/helpers.h>

enum {
    TCP_SENDMSG,
    TCP_RECVMSG
} tcp_kernel;

// avoiding linux/tcp.h which causes docker compilation problems
struct tcphdr {
    __be16 source;
    __be16 dest;
    __be32 seq;
    __be32 ack_seq;
    __u16 res1:4, doff:4, fin:1, syn:1, rst:1, psh:1, ack:1, urg:1, ece:1, cwr:1;
    __be16 window;
    __sum16 check;
    __be16 urg_ptr;
};


// Create a data structure to hold tcp information
struct event_data {
    __u32 src_ip;
    __u32 dest_ip;
    __u16 src_port;
    __u16 dest_port;
    __u32 pid;
};


int trace_tcp_sendmsg(struct pt_regs *ctx, struct sock *sk, struct sk_buff *skb) {
    struct iphdr *iph;
    struct tcphdr *tcph;

    // Check if skb and sk are not NULL
    if (!skb || !sk) {
        return 0;
    }

    // Extract IP and TCP headers from the skb
    iph = (struct iphdr *)(skb->data + skb->network_header);
    tcph = (struct tcphdr *)(skb->data + skb->transport_header);
       
    // Send data to user space
    bpf_trace_printk("tcp_sendmsg src=%pI4  port=%d ", &iph->saddr, bpf_ntohs(tcph->source));
    bpf_trace_printk("tcp_sendmsg dest=%pI4 port=%d", &iph->daddr, bpf_ntohs(tcph->dest));
    bpf_trace_printk("fnc:%d src:%d dst:%d", TCP_SENDMSG, &iph->daddr, &iph->daddr);

    struct bpf_map_def events;

    struct event_data data = {
        .src_ip = iph->saddr,
        .dest_ip = iph->daddr,
        .src_port = bpf_ntohs(tcph->source),
        .dest_port = bpf_ntohs(tcph->dest),
        .pid = bpf_get_current_pid_tgid(),
    };  

    //bpf_perf_event_output(skb, &events, BPF_F_CURRENT_CPU, &data, sizeof(data));

    return 0;
}


int trace_tcp_recvmsg(struct pt_regs *ctx, struct sock *sk, struct sk_buff *skb) {
    struct iphdr *iph;
    struct tcphdr *tcph;

    // Check if skb and sk are not NULL
    if (!skb || !sk) {
        return 0;
    }

    // Extract IP and TCP headers from the skb
    iph = (struct iphdr *)(skb->data + skb->network_header);
    tcph = (struct tcphdr *)(skb->data + skb->transport_header);

    bpf_trace_printk("tcp_recvmsg src %pI4 port=%d", &iph->saddr, bpf_ntohs(tcph->source));
    bpf_trace_printk("tcp_recvmsg dest %pI4 port=%d", &iph->daddr, bpf_ntohs(tcph->dest));
    bpf_trace_printk("fnc:%d src:%d dst:%d", TCP_RECVMSG, &iph->daddr, &iph->daddr);


    char json_msg[128];
    const char *event_type = "tcp_recvmsg";
    const char *syscall_name = "trace_tcp_recvmsg";
    int pid = bpf_get_current_pid_tgid();
    const char *msg = "Connection established";

    // Print formatted values into the buffer
    // int len = snprintf(json_msg, sizeof(json_msg), "Value: %d, Text: %s", pid, event_type);

    // Manually format the JSON-like message
    //int len = bpf_probe_read_str(json_msg, sizeof(json_msg), "{ type: %s, syscall: %s, pid: %d, message: %s }", event_type, syscall_name, pid, msg);

    // Null-terminate the string
    //if (len < sizeof(json_msg))
    //    json_msg[len] = 0;

    // Print the formatted message
    //bpf_trace_printk("%s\\n", json_msg);

    return 0;
}


"""

b = BPF(text=prog)

b.attach_kprobe(event="tcp_sendmsg", fn_name="trace_tcp_sendmsg")
b.attach_kprobe(event="tcp_recvmsg", fn_name="trace_tcp_recvmsg")

b.trace_print()

# This prints out a trace line every time the clone system call is called

# If you rename hello() to kprobe__sys_clone() you can delete the
# b.attach_kprobe() line, because bcc can work out what event to attach this to
# from the function name.