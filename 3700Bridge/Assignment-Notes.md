The solution must:

- [ ] Form a spanning tree in order to prevent packet loops
  * Fast convergence: Require little time to form or update a spanning tree. 
  * Low overhead: Reduce packet flooding and unnecessary transmissions when possible
- [ ] Handle the failure of bridges and the introduction of new bridges and LANs over time
- [ ] Learn the locations (port numbers) of end hosts
- [ ] Deliver end host packets to the destination
- [ ] Handle the mobility of end hosts between LANs
- [ ] Print out specific debugging messages to STDOUT

Potential Hangups:
* Note that your bridge could have multiple ports connected to the same LAN, 
meaning one port will hear the other port’s messages