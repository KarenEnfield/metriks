# Metriks

eBPF for Docker Desktop on macOS

eBPF and its compiler bcc need access to some parts of the kernel and its headers to work. This image shows how you can do that with Docker Desktop for mac's linuxkit host VM.

Build the image

Done quite simply with:

docker build -t ebpf-for-mac .

Run the image

It needs to run as privileged, and depending on what you want to do, having access to the host's PID namespace is pretty useful too.

docker run -it --rm \ 
  --privileged \ 
  -v /lib/modules:/lib/modules:ro \ 
  -v /etc/localtime:/etc/localtime:ro \ 
  --pid=host \ 
  ebpf-for-mac
Note: /lib/modules probably doesn't exist on your mac host, so Docker will map the volume in from the linuxkit host VM.



# To build

1. Install Dependencies:
Make sure you have the necessary dependencies installed. You can use Homebrew for this:
Install llvm
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
brew install llvm bcc

Install bcc
brew install bcc
brew install --cask icc 

Install bpf
brew install bpftrace
brew install potrace
brew install bcc-tools
brew install --cask box-tools



2. Set Environment Variables:
BCC expects LLVM libraries to be in specific locations.
Add the following lines to your shell profile file (e.g., ~/.bash_profile or ~/.zshrc):
export LLVM_CONFIG=/usr/local/opt/llvm/bin/llvm-config
export CLANG=/usr/local/opt/llvm/bin/clang

3. Write an eBPF Program:
Write your eBPF program in a C file. For example, create a file named basic_ebpf.c:

For Linux:
    // basic_ebpf.c
    #include <uapi/linux/bpf.h>

    SEC("tracepoint/syscalls/sys_enter_execve")
    int tracepoint__sys_enter_execve(void *ctx) {
        bpf_trace_printk("Hello, eBPF!\n");
        return 0;
    }

 For Mac:
    // basic_ebpf.c
    #include <stdio.h>
    #include <stdlib.h>
    #include <stdint.h>
    #include <string.h>
    #include <unistd.h>
    #include <sys/time.h>
    #include <sys/resource.h>
    #include <bpf/bpf.h>

    int main(void) {
        printf("Hello, eBPF on macOS!\n");

        // Your eBPF logic goes here

        return 0;
    }

or an example with ebpf logic 
    // basic_ebpf.c
    #include <stdio.h>
    #include <stdlib.h>
    #include <stdint.h>
    #include <string.h>
    #include <unistd.h>
    #include <sys/time.h>
    #include <sys/resource.h>
    #include <bpf/bpf.h>

    int main(void) {
        printf("Hello, eBPF on macOS!\n");

        // Load eBPF program (dummy logic for illustration purposes)
        const char* prog_code = "int kprobe__icmp6_rcv(void *ctx) { return 0; }";
        int prog_fd = bpf_prog_load(BPF_PROG_TYPE_KPROBE, prog_code, strlen(prog_code), "GPL", 0, NULL, 0);
        if (prog_fd < 0) {
            perror("Failed to load eBPF program");
            return 1;
        }

        // Attach eBPF program to network interface (dummy interface for illustration purposes)
        const char* interface = "en0";
        int attach_result = bpf_attach_socket(prog_fd, BPF_SK_MSG_VERDICT, interface);
        if (attach_result < 0) {
            perror("Failed to attach eBPF program to the network interface");
            return 1;
        }

        printf("eBPF program attached to network interface %s\n", interface);

        // Wait for program to capture packets (dummy loop for illustration purposes)
        printf("Waiting for packets... (Ctrl+C to exit)\n");
        while (1) {
            sleep(1);
        }

        return 0;
    }


4. Compile the eBPF Program:
Compile the eBPF program using the BCC compiler:
clang -O2 -target bpf -c basic_ebpf.c -o basic_ebpf.o

For macOS
clang -o basic_ebpf basic_ebpf.c -lbpf
./basic_ebpf


5. Run the eBPF Program:
Load and run the eBPF program using the bcc tools:


sudo bccperf --tracepoint=syscalls:sys_enter_execve ./basic_ebpf.o
