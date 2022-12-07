# Router Project

This project has been created for the CS3700 router [project](https://3700.network/docs/projects/router/).

It simulates the functionality of a Router.

## Approach

* Every packet received by this router is deserialized into a [Packet](./networks/packet.py) object for guaranteed packet structure and 
ease of variable access:

```python
class PacketType(str, Enum):
    UPDATE = "update"
    DATA = "data"
    ...    
    WITHDRAW = "withdraw"
    
@dataclass(frozen=True)
class WithdrawMsg(Deserializable, Serializable):
    network: IPAddress  # "<network prefix>"             ... Example: 12.0.0.0
    netmask: IPAddress  # "<associated subnet mask>"     ... Example: 255.0.0.0

...

@dataclass(frozen=True)
class Packet(Deserializable, Serializable):
    """
    Representation of a Packet as defined in https://3700.network/docs/projects/router/
    """
    src: IPAddress
    dst: IPAddress
    type: PacketType
    msg: ConditionalField = ConditionalField(var_name="type",
                                             mapping={
                                                 PacketType.UPDATE: UpdateMsg,
                                                 PacketType.DATA: Any,
                                                 ...
                                                 PacketType.WITHDRAW: List[WithdrawMsg]
                                             })
```

1. Each raw packet is received in a group by the router using the `select` library
2. The deserialized packet type declaration (as seen above) is used to sort each deserialized packet into a respective 
handler 
3. Once the router has generated handlers for the entire packet grouping, the handlers are all activated to process 
their packets

### Goals

* Accept route update messages from the BGP neighbors, and forward updates as appropriate
* Accept route revocation messages from the BGP neighbors, and forward revocations as appropriate
* Forward data packets towards their correct destination
* Return error messages in cases where a data packet cannot be delivered
* Coalesce forwarding table entries for networks that are adjacent and on the same port
* Serialize your routing table cache so that it can be checked for correctness
* Your program must be called 3700router

### Helpful Submission Commands

`zip -r p2.zip 3700router Makefile README.md networks -x networks/__pycache__\* networks/__init__.py`