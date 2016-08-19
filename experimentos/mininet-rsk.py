from time import sleep
from mininet.topo import Topo
from mininet.net import Mininet
from mininet.log import setLogLevel
from mininet.node import RemoteController
from mininet.node import OVSSwitch
from mininet.link import TCLink


import random
import re

#
# Fat-tree topology implemention for mininet
#
class FatTree(Topo):
    def randByte(self):
        return hex(random.randint(0, 255))[2:]

    def makeMAC(self, i):
        return self.randByte() + ":" + self.randByte() + ":" + \
               self.randByte() + ":00:00:" + hex(i)[2:]

    def makeDPID(self, i):
        a = self.makeMAC(i)
        dp = "".join(re.findall(r'[a-f0-9]+', a))
        return "0" * (12 - len(dp)) + dp

    # args is a string defining the arguments of the topology!
    # has be to format: "x,y,z" to have x hosts and a bw limit of y for
    # those hosts each and a latency of z (in ms) per hop
    def __init__(self, hosts=2, bwlimit=10, lat=0.1, **opts):
        Topo.__init__(self, **opts)
        tor = []
        numLeafes = hosts
        bw = bwlimit
        s = 1
        #bw = 10
        for i in range(numLeafes):
            h = self.addHost('h' + str(i + 1), mac=self.makeMAC(i),
                            ip="10.0.0." + str(i + 1))
            sw = self.addSwitch('s' + str(s), dpid=self.makeDPID(s),
                                **dict(listenPort=(13000 + s - 1)))
            s = s + 1
            self.addLink(h, sw, bw=bw, delay=str(lat) + "ms")
            #self.addLink(h, sw, bw=bw, delay=10)
            tor.append(sw)
        toDo = tor  # nodes that have to be integrated into the tree
        while len(toDo) > 1:
            newToDo = []
            for i in range(0, len(toDo), 2):
                sw = self.addSwitch('s' + str(s), dpid=self.makeDPID(s),
                                    **dict(listenPort=(13000 + s - 1)))
                s = s + 1
                newToDo.append(sw)
                #self.addLink(toDo[i], sw, bw=bw, delay=str(lat) + "ms")
                self.addLink(toDo[i], sw, bw=bw, delay=1000)
                if len(toDo) > (i + 1):
                    self.addLink(toDo[i + 1], sw, bw=bw, delay=str(lat) + "ms")
                    #self.addLink(toDo[i + 1], sw, bw=bw, delay=1000)
            toDo = newToDo
            bw = 2.0 * bw


class SingleSwitchTopo(Topo):
  "Single switch connected to n hosts."
  def build(self, n=2):
    switch = self.addSwitch('s1')
    # Python's range(N) generates 0..N-1
    for h in range(n):
      host = self.addHost('h%s' % (h + 1))
      self.addLink(host, switch)

def simpleTest():
  "Create and test a simple network"
  total_time =  60
  n = 3
  topo = FatTree(n, 10, 1)
  net = Mininet(topo, controller=lambda name: RemoteController( name, ip='192.168.0.100',port=6633 ), switch=OVSSwitch, link=TCLink)
  net.start()
  
  hosts = [net.get("h%d" % i) for i in range(1, n+1)]

  for h in hosts:
    print "Host %s has ip %s" % (h.name, h.IP())

  cmd = [""] * n
  
  cmd[0]   = "timeout 60 /home/maxinet/rsk/node -n 100 -dst='%s:30305' -lst='%s:30305' --start -h %s > /home/maxinet/rsk/log%s 2>&1 &" % (hosts[1].IP(), hosts[0].IP(), hosts[0].name, hosts[0].name)
  for i in xrange(1, n):
    cmd[i] = "timeout 65 /home/maxinet/rsk/node -n 105 -dst='%s:30305' -lst='%s:30305'         -h %s > /home/maxinet/rsk/log%s 2>&1 &" % (hosts[(i + 1) % n].IP(), hosts[i].IP(), hosts[i].name, hosts[i].name)

  for i in xrange(1, n):
    print cmd[i], hosts[i].cmd(cmd[i])
  sleep(5)
  print "Starting Experiment"
  print cmd[0], hosts[0].cmd(cmd[0])
  
  sleep(total_time + 5)
  net.stop()

if __name__ == "__main__":
  setLogLevel('info')
  simpleTest()
