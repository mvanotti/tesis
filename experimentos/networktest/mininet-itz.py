from time import sleep
from mininet.topo import Topo
from mininet.topolib import TreeTopo
from mininet.net import Mininet
from mininet.log import setLogLevel
from mininet.node import RemoteController
from mininet.node import OVSSwitch, OVSKernelSwitch
from mininet.link import TCLink
from cogentco import GeneratedTopo
from random import sample


import random
import re

def simpleTest():
  "Create and test a simple network"
  total_time = 60 * 5
  topo = GeneratedTopo()
  #topo = TreeTopo( depth=7, fanout=2 )
  net = Mininet(topo, controller=lambda name: RemoteController( name, ip='127.0.0.1',port=6633 ), switch=OVSKernelSwitch, link=TCLink)
  #net = Mininet(topo, switch=OVSKernelSwitch, link=TCLink)
  net.start()
  
  hosts = net.hosts
  hosts = sample(hosts, 32)

  with open("peers", "w") as f:
    for h in hosts:
      print "Host %s has ip %s" % (h.name, h.IP())
      f.write("%s:%d\n" % (h.IP(), 5020))

  sleep(60 * 2)
  res = net.pingFull(hosts=hosts)
  sleep(60 * 2)
  res = net.pingFull(hosts=hosts)
  sleep(60 * 2)

  cmd = {}
  for i in range(len(hosts)):
    c = """timeout %d /home/mvanotti/tesis/repo/experimentos/networktest/node -h %d > /tmp/pruebas/%d.test 2>&1 &""" % (total_time, i, i)
    cmd[hosts[i].name] = c
    
  for h in hosts:
    if h.name not in cmd: continue
    print cmd[h.name], h.cmd(cmd[h.name])
  sleep(total_time + 60)

  net.stop()

if __name__ == "__main__":
  setLogLevel('info')
  simpleTest()
