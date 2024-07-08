#ifndef TCP_HDR
#define TCP_HDR 1
// avoiding linux/tcp.h include which causes docker compilation problems
struct tcphdr {
    __be16 source;
    __be16 dest;
    __be32 seq;
    __be32 ack_seq;
    __u8 doff_res1;
    __u8 flags;
    __be16 window;
    __sum16 check;
    __be16 urg_ptr;
};
#endif

/* in tcp 'flags' bit fields for LITTLE_ENDIAN are
FIN (0x01)
SYN (0x02)
RST (0x04)
PSH (0x08)
ACK (0x10)
URG (0x20)
ECE (0x40)
CWR (0x80)

These flags are bitfields within a 16-bit field, with different layouts for little-endian and big-endian systems.

fin: FIN flag, indicating no more data from sender.

syn: SYN flag, used to initiate connections.

rst: RST flag, used to reset connections.

psh: PSH flag, indicating the push function.

ack: ACK flag, indicating the acknowledgment field is significant.

urg: URG flag, indicating urgent pointer field is significant.

ece: ECE flag, used for explicit congestion notification echo.

cwr: CWR flag, used for congestion window reduced.

*/