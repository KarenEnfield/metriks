
#include <uapi/linux/ptrace.h>
#include <linux/skbuff.h>
#include <linux/ip.h>
#include <bcc/helpers.h>

#define TASK_COMM_LEN 16 // avoiding including linux/bpf.h

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
struct event_data_t {
    u32 src_ip;
    u32 dest_ip;
    u16 src_port;
    u16 dest_port;
    u32 pid;
    u64 timeoffset_ns; // nanosecond offset since last system boot   
    char comm[TASK_COMM_LEN];
    char event_name[TASK_COMM_LEN];
};

// Define the output map for communication with user space
BPF_PERF_OUTPUT(events);

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
       
    // Print data to user space
    bpf_trace_printk("tcp_sendmsg src=%pI4  port=%d ", &iph->saddr, bpf_ntohs(tcph->source));
    bpf_trace_printk("tcp_sendmsg dest=%pI4 port=%d", &iph->daddr, bpf_ntohs(tcph->dest));
    
    struct event_data_t data = {
        .src_ip = iph->saddr,
        .dest_ip = iph->daddr,
        .src_port = bpf_ntohs(tcph->source),
        .dest_port = bpf_ntohs(tcph->dest),
        .pid = bpf_get_current_pid_tgid(),
        .timeoffset_ns = bpf_ktime_get_ns(), 
    };  

    // Copy comm name into event data
    bpf_get_current_comm(&data.comm, sizeof(data.comm));
    
    // Copy event name to event data
    bpf_probe_read_str(&data.event_name, sizeof(data.event_name), "tcp_sendmsg");

    // Send the data to user space
    events.perf_submit(ctx, &data, sizeof(struct event_data_t));

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
    
    // Create event data to send to userspace
    struct event_data_t data = {
        .src_ip = iph->saddr,
        .dest_ip = iph->daddr,
        .src_port = bpf_ntohs(tcph->source),
        .dest_port = bpf_ntohs(tcph->dest),
        .pid = bpf_get_current_pid_tgid(),
        .timeoffset_ns = bpf_ktime_get_ns(),
    };  

    // Copy comm name into event data
    bpf_get_current_comm(&data.comm, sizeof(data.comm));

    // Copy event name to event data
    bpf_probe_read_str(&data.event_name, sizeof(data.event_name), "tcp_recvmsg");

    // Send the data to user space
    events.perf_submit(ctx, &data, sizeof(struct event_data_t));

    return 0;
}

