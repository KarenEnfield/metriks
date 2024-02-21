#include <uapi/linux/ptrace.h>
#include <linux/skbuff.h>
#include <linux/ip.h>

#define TASK_PAYLOAD_SIZE 128

// avoiding linux/tcp.h which causes docker compilation problems
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

struct event_t {
    u16 event_id;       // tcp Event type 1 = tcp_sendmsg, 2 = tcp_recvmsg
    u32 src_ip;         // Source IP address
    u32 dest_ip;        // Destination IP address
    u16 src_port;       // Source port number in the TCP header
    u16 dest_port;      // Destination port number in the TCP header
    u32 pid;            // Process ID == Thread group id in bpf
    u32 tid;           // Thread ID
    u64 timeoffset_ns;      // Timestamp
    u16 flags;          // Flags field in the TCP header (URG, ACK, PSH, RST, SYN, FIN)
    u32 seq;        // Sequence number in the TCP header
    u32 ack;        // Acknowledgment number in the TCP header
    u16 window;    // Window size in the TCP header
    u32 payload_size;
    char payload[TASK_PAYLOAD_SIZE];  // Adjust the size based on your payload size  
    // Add other fields as needed
};

BPF_PERF_OUTPUT(events);

int trace_tcp_sendmsg(struct pt_regs *ctx, struct sock *sk, struct sk_buff *skb) {
    
    unsigned short event_id=1;

    struct tcphdr *tcph = (struct tcphdr *)(skb->data + skb->transport_header);
    struct iphdr *iph = (struct iphdr *)(skb->data + skb->network_header);

    u64 pid_tgid = bpf_get_current_pid_tgid();    
    
    struct event_t event = {
        .event_id = event_id,
        .src_ip = iph->saddr,
        .dest_ip = iph->daddr,
        .src_port = bpf_ntohs(tcph->source),
        .dest_port = bpf_ntohs(tcph->dest),
        .pid = pid_tgid >> 32,    // Lower 32 bits
        .tid = pid_tgid & 0xFFFFFFFF, // Upper 32 bits
        .timeoffset_ns = bpf_ktime_get_ns(),
        .flags = tcph->flags,        // Flags field in the TCP header (URG, ACK, PSH, RST, SYN, FIN)
        .seq = bpf_ntohl(tcph->seq),           // Sequence number in the TCP header
        .ack = bpf_ntohl(tcph->ack_seq),       // Acknowledgment number in the TCP header
        .window = bpf_ntohs(tcph->window),     // Window size in the TCP header
        .payload_size = skb->len
    };
    
    // get a few bytes of payload data for userspace analysiz, if it is a valid range of data
    bpf_probe_read(&event.payload, sizeof(event.payload), &skb->data);

    // Send event data to the userspace  
    events.perf_submit(ctx, &event, sizeof(struct event_t));
    
    // events send alternative
    //bpf_perf_event_output(skb, &events, BPF_F_CURRENT_CPU, &event, sizeof(event));

    return 0;
}

int trace_tcp_recvmsg(struct pt_regs *ctx, struct sock *sk, struct sk_buff *skb) {    

    unsigned short event_id = 2;

    struct tcphdr *tcph = (struct tcphdr *)(skb->data + skb->transport_header);
    struct iphdr *iph = (struct iphdr *)(skb->data + skb->network_header);

    u64 pid_tgid = bpf_get_current_pid_tgid();
    
    struct event_t event = {
        .event_id = event_id,
        .src_ip = iph->saddr,
        .dest_ip = iph->daddr,
        .src_port = bpf_ntohs(tcph->source),
        .dest_port = bpf_ntohs(tcph->dest),
        .pid = pid_tgid >> 32,
        .tid = pid_tgid & 0xFFFFFFFF,
        .timeoffset_ns = bpf_ktime_get_ns(),
        .flags = tcph->flags,        // Flags field in the TCP header (URG, ACK, PSH, RST, SYN, FIN)
        .seq = bpf_ntohl(tcph->seq),           // Sequence number in the TCP header
        .ack = bpf_ntohl(tcph->ack_seq),       // Acknowledgment number in the TCP header
        .window = bpf_ntohs(tcph->window),     // Window size in the TCP header
        .payload_size = skb->len 
    };

    // get a few bytes of payload data for userspace analysis
    bpf_probe_read(&event.payload, sizeof(event.payload), &skb->data);
   
    // Send event data to the userspace
    events.perf_submit(ctx, &event, sizeof(struct event_t));
    
    return 0;
}
