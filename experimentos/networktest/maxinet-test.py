from time import sleep

from MaxiNet.Frontend import maxinet
from mininet.topo import Topo
from MaxiNet.tools import FatTree
from MaxiNet.tools import Tools
from mininet.node import OVSSwitch
from mininet.link import TCLink

def simpleTest():
  "Create and test a simple network"
  total_time = 20 * 1
  max_nodes_per_worker = 3
  n = 10
  topo = FatTree(n, 10, 1)

  cluster = maxinet.Cluster()
  exp = maxinet.Experiment(cluster, topo, switch=OVSSwitch)
  exp.setup()
  
  hosts = [exp.get_node("h%d" % i) for i in range(1, n+1)]
  with open("/home/maxinet/rsk/rsk/networktest/peers", "w") as f:
    for h in hosts:
      print "Host %s has ip %s" % (h.name, h.IP())
      f.write("%s:%d\n" % (h.IP(), 5020))

  print("waiting 20 seconds for routing algorithms on te controller to converge")
  sleep(20)
  print("Starting experiment!!")

  cmd = {}
  for i in range(len(hosts)):
    h = hosts[i]
    c = """timeout %d /home/maxinet/rsk/rsk/networktest/node -f /home/maxinet/rsk/rsk/networktest/peers -h %d > /home/maxinet/rsk/rsk/networktest/logs/%d.test 2>&1 &""" % (total_time, i, i)
    cmd[h.name] = c
    
  for h in hosts:
    print(cmd[h.name], h.cmd(cmd[h.name]))

  sleep(total_time + 10)
  exp.stop()

if __name__ == "__main__":
  simpleTest()
