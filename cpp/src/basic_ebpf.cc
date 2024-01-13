// basic_ebpf.c
#include <linux/bpf.h>

SEC("filter")
int basic_ebpf(struct __sk_buff *skb) {
    // Your eBPF logic goes here
    return XDP_PASS;  // Allow the packet
}
