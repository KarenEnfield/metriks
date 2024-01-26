#!/usr/bin/env python3

from bcc import BPF

bpf = BPF(src_file="bpf_collector.c")

bpf.attach_kprobe(event="tcp_sendmsg", fn_name="trace_tcp_sendmsg")
bpf.attach_kprobe(event="tcp_recvmsg", fn_name="trace_tcp_recvmsg")

bpf.trace_print()

# This prints out a trace line every time the tcp clones are called
