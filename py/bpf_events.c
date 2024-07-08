#include <linux/ptrace.h>
#include <linux/skbuff.h>
#include <linux/sched.h>
#include <linux/if_ether.h>
#include <linux/ip.h>
#include "my_tcphdr.h"

#define MAX_DATA_SIZE 64
#define DOFF_MASK 0xF0
#define DOFF_SHIFT 4


struct bpf_event_t {
    u8 id;
    u32 pid;
    u32 tgid;
    u32 saddr;
    u32 daddr;
    u16 sport;
    u16 dport;
    u64 latency;
    char comm[TASK_COMM_LEN];
    char payload[MAX_DATA_SIZE]; // capture first 64 bytes of payload for example
    u16 http_status;
    int copied;
    u8  doff;
    u8  flags;
    u32 window_size;
};

BPF_PERF_OUTPUT(connect_events);

int trace_tcp_connect(struct pt_regs *ctx, struct sock *sk, struct sk_buff *skb) {
    // Setup headers
    struct tcphdr *tcph = (struct tcphdr *)(skb->data + skb->transport_header);
    struct iphdr *iph = (struct iphdr *)(skb->data + skb->network_header);

    // Initialize values
    struct bpf_event_t event = {};
    u64 pid_tgid = bpf_get_current_pid_tgid();
    int copied = PT_REGS_RC(ctx);

    // Assign event fields
    event.id = 1;
    event.pid = pid_tgid >> 32;    // Lower 32 bits;
    event.tgid = pid_tgid & 0xFFFFFFFF; // Upper 32 bits
    event.saddr = iph->saddr;
    event.daddr = iph->daddr;
    event.sport = bpf_ntohs(tcph->source);
    event.dport = bpf_ntohs(tcph->dest);
    event.latency = bpf_ktime_get_ns();
    bpf_get_current_comm(&event.comm, sizeof(event.comm));// Get the current comm
    event.copied = copied;
    event.flags = tcph->flags;
    event.window_size = bpf_ntohs(tcph->window);
    
    // Get the Payload

    // Calculate the TCP header length
    int data_offset = (tcph->doff_res1 & DOFF_MASK) >> DOFF_SHIFT;
    size_t tcp_header_length = data_offset * 4;
    
    // Calculate the payload pointer
    __u8 *payload = (__u8 *)tcph + tcp_header_length;

    // Get a few bytes of payload data for userspace analysis
    bpf_probe_read(&event.payload, sizeof(event.payload), payload);
    
    // Check for "HTTP" in the payload, to set the http status code
    if (event.payload[0] == 'H' && event.payload[1] == 'T' && event.payload[2] == 'T' && event.payload[3] == 'P') {
        int http_code_0 = event.payload[9]-'0';  // First digit of status code
        int http_code_1 = event.payload[10]-'0'; // Second digit of status code
        int http_code_2 = event.payload[11]-'0'; // Third digit of status code
        event.http_status = (u16)(http_code_2 * 100 + http_code_1 * 10 + http_code_0);
    }
    
    // Submit a tcp event
    connect_events.perf_submit(ctx, &event, sizeof(event));
    return 0;
}

BPF_PERF_OUTPUT(http_events);
BPF_PERF_OUTPUT(tcp_events);

// only process as a potential http event if there is payload data

int trace_tcp_recvmsg(struct pt_regs *ctx, struct sock *sk, struct sk_buff *skb) {
    // Setup the headers 
    struct tcphdr *tcph = (struct tcphdr *)(skb->data + skb->transport_header);
    struct iphdr *iph = (struct iphdr *)(skb->data + skb->network_header); 
    
    // Initialize the values
    struct bpf_event_t event = {};  
    u64 pid_tgid = bpf_get_current_pid_tgid();
    int data_offset = (tcph->doff_res1 & DOFF_MASK) >> DOFF_SHIFT;
    int copied = PT_REGS_RC(ctx);
    
    if (copied<=0)
        return 0;

    // Assign event field values
    event.id = 2;
    event.pid = pid_tgid >> 32;    // Lower 32 bits;
    event.tgid = pid_tgid & 0xFFFFFFFF; // Upper 32 bits
    event.saddr = iph->saddr,
    event.daddr = iph->daddr,
    event.sport = bpf_ntohs(tcph->source),
    event.dport = bpf_ntohs(tcph->dest),
    event.latency = bpf_ktime_get_ns();
    bpf_get_current_comm(&event.comm, sizeof(event.comm)); // Get the current comm
    event.copied = copied;
    event.doff = data_offset;
    event.flags = tcph->flags;
    event.window_size = bpf_ntohs(tcph->window);

    // Get the payload

    // Calculate the TCP header length
    size_t tcp_header_length = data_offset * 4;

    // Use to Calculate the payload pointer
    __u8 *payload = (__u8 *)tcph + tcp_header_length;

    // Get a few bytes of payload data, if it is a valid range of data
    bpf_probe_read(&event.payload, sizeof(event.payload), payload);

    // Check for "HTTP" in the payload to set the HTTP status code
    if (event.payload[0] == 'H' && event.payload[1] == 'T' && event.payload[2] == 'T' && event.payload[3] == 'P') {
        int http_code_0 = event.payload[9]-'0';  // First digit of status code
        int http_code_1 = event.payload[10]-'0'; // Second digit of status code
        int http_code_2 = event.payload[11]-'0'; // Third digit of status code
        event.http_status = (u16)(http_code_2 * 100 + http_code_1 * 10 + http_code_0);
        
        // Submit an http eventt
        http_events.perf_submit(ctx, &event, sizeof(event));
    }
    else 
        // Submit a tcp event
        tcp_events.perf_submit(ctx, &event, sizeof(event));
    
    
    return 0;
}


BPF_PERF_OUTPUT(udp_events);

int trace_udp_sendmsg(struct pt_regs *ctx, struct sock *sk, struct sk_buff *skb) {
    // Setup the headers
    struct tcphdr *tcph = (struct tcphdr *)(skb->data + skb->transport_header);
    struct iphdr *iph = (struct iphdr *)(skb->data + skb->network_header);

    // Initialize values
    struct bpf_event_t event = {};
    u64 pid_tgid = bpf_get_current_pid_tgid();
    int copied = PT_REGS_RC(ctx);

    // Assign event field values
    event.id = 3;
    event.pid = pid_tgid >> 32;    // Lower 32 bits;
    event.tgid = pid_tgid & 0xFFFFFFFF; // Upper 32 bits
    event.saddr = iph->saddr;
    event.daddr = iph->daddr;
    event.sport = bpf_ntohs(tcph->source);
    event.dport = bpf_ntohs(tcph->dest);
    event.latency = bpf_ktime_get_ns();
    bpf_get_current_comm(&event.comm, sizeof(event.comm)); // Get the current comm
    event.copied = copied;

    // Get the payload
    bpf_probe_read(&event.payload, sizeof(event.payload), &skb->data);

    // Check for "HTTP" in the payload to set the HTTP status code
    if (event.payload[0] == 'H' && event.payload[1] == 'T' && event.payload[2] == 'T' && event.payload[3] == 'P') {
        int http_code_0 = event.payload[9]-'0';  // First digit of status code
        int http_code_1 = event.payload[10]-'0'; // Second digit of status code
        int http_code_2 = event.payload[11]-'0'; // Third digit of status code
        event.http_status = (u16)(http_code_2 * 100 + http_code_1 * 10 + http_code_0);
    }

    // Submit a udp event
    udp_events.perf_submit(ctx, &event, sizeof(event));
    return 0;
}


BPF_PERF_OUTPUT(dns_events);

int trace_dns_query(struct pt_regs *ctx, struct sock *sk, struct sk_buff *skb) {
    // Setup the headers
    struct tcphdr *tcph = (struct tcphdr *)(skb->data + skb->transport_header);
    struct iphdr *iph = (struct iphdr *)(skb->data + skb->network_header);

    // Initialize the values
    struct bpf_event_t event = {};
    u64 pid_tgid = bpf_get_current_pid_tgid();
    int copied = PT_REGS_RC(ctx);

    // Assign the event fields
    event.id = 4;
    event.pid = pid_tgid >> 32;    // Lower 32 bits;
    event.tgid = pid_tgid & 0xFFFFFFFF; // Upper 32 bits
    event.saddr = iph->saddr;
    event.daddr = iph->daddr;
    event.sport = bpf_ntohs(tcph->source);
    event.dport = bpf_ntohs(tcph->dest);
    event.latency = bpf_ktime_get_ns();
    bpf_get_current_comm(&event.comm, sizeof(event.comm));
    event.copied = copied;

    // Submit a dns event
    dns_events.perf_submit(ctx, &event, sizeof(event));
    return 0;
}
