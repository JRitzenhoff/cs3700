# TCP Implementation

To minimize the data send, all packets are sent as raw bytes and encoding/decoded to UTF-8 values using 
the Python `struct` module.

A [`TCPPacket`](./networks/packet.py#L135-L195) consists of a [`TCPHeader`](./networks/packet.py#L95-L132), 
a data byte count, and the raw data bytes. The `TCPHeader` is based on that shown in the Network Powerpoint Slides.

The sender progressively reads from the STDIN until the number of sent packets matches the appropriate sliding window.
Upon receiving an ACK or NACK the sender resends a packet or reads from STDIN and sends a new packet accordingly.

Depending on the flow-rate of the packets, the sender and receiver will fill their sliding windows.


## Determining RTT
Every packet header contains a series of flags. 

The sender always includes a `TCPPacket.sequence_number` and the `TCPFlag.SYNCHRONIZATION`.
The receiver always responds with the same `TCPPacket.sequence_number` and the `TCPFlag.ACKNOWLEDGEMENT` if 
the packet has been received properly.

In the case of a receiver error, the receiver will respond with the same sequence number and a `TCPFlag.ERROR` along
with the specific error (i.e. `TCPFlag.CHECKSUM_ERROR`)

By looking at the sequence number of a returned packet, the round-trip time is calculated.

### Helpful Submission Commands

`zip -r p4.zip 3700recv 3700send Makefile README.md networks -x networks/__pycache__\* networks/__init__.py`