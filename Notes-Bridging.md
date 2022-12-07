
# Components

`zip -r milestone2.zip 3700bridge Makefile networks -x networks/__pycache__\* networks/__init__.py `

## Brain Dump

* Bridge declares that it is the root
* Bridge sends out BPDUs
* Bridge receives BPDUs
  * Take the smallest and declare that as the root node
    (could be the bridge itself)
  
  * For every port:
    * If it is NOT the smallest in its LAN
      * Turn that port off
  
    * If it is the smallest, assign it 
    




## Forwarding Table

This contains information relevant for forwarding
DATA messages

| SRC MAC Address   | Port  | Age   |
|-------------------|-------|-------|
| 00:00:00:00:00:AA | 1     | 1 min |
| 00:00:00:00:00:BB | 2     | 7 min |

#### Actual Forwarding






* If the port has the best BPDU of any on it's LAN
    that port is the designated (should send to root)

* If the port does NOT have the best BPDU of any it's LAN
    that port can ignore all calls that arrive on it
  * This is because the designated will take care of it


* Every port can do this individually?
  * After the BPDU's have been updated
  * Loop through the ports:
    * If the last sent BPDU is the lowest of all the received
        this port stays open









* If a destination is in the forwarding table, 
send only to the destination port

* If a destination is NOT in the forwarding table,
send to ALL ports (except the original sender)

## Spanning Tree

Algorithm:
1. Elect a bridge to be the root of the tree
2. Ever bridge finds shortest path to the root
3. Union of these paths becomes the spanning tree

The bridge doesn't need an actual spanning tree...
* Need a Root Bridge ID and a Cost to Root
  * If a new BPDU arrives with a lower bridge ID or a lower cost to root
    then, change what's saved
  * Close ports that have equal distances to the root ID
  * Denote ports with a larger cost as "receivers"
  * Denote the singular port with a smaller cost as a "sender"
  * If there are two ports with the same lower cost... arbitrarily pick the one with a lower id


## Building the bridge

1. Send out a Bridge Protocol Data Unit (BPDU) to all ports
2. Receive a set of BPDU's from all ports
   1. Figure out who has the lowest ID and is closest to the root
   2. Repeat until the tree is stable


## Brain-Dump

* For every BPDU read, save it
```python
from typing import List, Tuple, Dict
from networks.packet import BPDU

# get the bpdu that aligns with a requested port
past_bpdus: Dict[str, List[Tuple[int, int, BPDU]]] = {}

requested_id = '9a34'
relevant_bpdus = past_bpdus[requested_id]

new_bpdu = BPDU()

# should only be one bpdu
for port_index, count, existing_bpdu in relevant_bpdus:
    # if the port is the same  
    if new_bpdu.source_bridge_port == existing_bpdu.source_bridge_port:
        # check whether the existing_bpdu needs to be replaced
        #   OR
        # if the count needs to be increased
        pass
    else:
        # add to the relevant_bpdu list
        # ... this will need to be used at the end to close a port
        pass
```

```python
from typing import List, Tuple, Dict
from networks.packet import BPDU

class Port:
    def __init__(self):
        # [ (<count>, BPDU), ... ]
        self.seen_bpdus: List[Tuple[int, BPDU]] = []
        self.disabled = False

# if ALL the counts for EVERY port are greater than 2
#   then logic can be implemented to define and disable ports
        
# for every port, extract the seen_bpdus
#   if there are separate ports with some of the same seen
#   use that to disable
```
* On every bpdu


## Re-evaluation

* Every port should figure out its own shit
  * The bridge ONLY needs to figure ou what the root port is after BPDU's are received
* Every port should keep track of its most recently sent BPDU
  * This is because once bridges/LANs start dropping, there is bound to by a de-syncronization

* Disable a port if you think it should be disabled
  * Worst case-scenario, the port will be re-enabled on the next BPDU

* If the BPDU broadcast changes, flush the forwarding port
* If a port status changes, flush the BPDU

* IF there are two ports receiving from the same bridge...
  * They are on the same LAN. One port should receive the BPDU from another port AND can do a comparison
* 
