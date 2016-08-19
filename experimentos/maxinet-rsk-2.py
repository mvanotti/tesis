from time import sleep

from MaxiNet.Frontend import maxinet
from mininet.topo import Topo
from MaxiNet.tools import FatTree
from MaxiNet.tools import Tools
from mininet.node import OVSSwitch

      
def simpleTest():
  "Create and test a simple network"
  total_time = 60
  n = 20
  topo = FatTree(n, 10, 1)

  cluster = maxinet.Cluster()

  exp = maxinet.Experiment(cluster, topo, switch=OVSSwitch)
  exp.setup()
  print "Hostname mapping:", exp.generate_hostname_mapping()
  print "waiting 10 seconds for routing algorithms on te controller to converge"
  sleep(10)

  print "Starting experiment!!"

  hosts = [exp.get_node("h%d" % i) for i in range(1, n+1)]
  for h in hosts:
    print "For host ", h.name, " Worker is ", exp.get_worker(h).hn()
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

  """  
  for h1 in hosts:
    for h2 in hosts:
      if h1.name == h2.name: continue
      print "ping from %s to %s\n" % (h1.name, h2.name), h1.cmd("ping -c 1 %s" % h2.IP())
  sleep(5)
  """  
  """
  cmd1 = "timeout 15 /tmp/udp -dst='%s:30305' -lst='%s:30305' --client > /tmp/log1 2>&1 &" % (hosts[1].IP(), hosts[0].IP())
  cmd2 = "timeout 15 /tmp/udp -dst='%s:30305' -lst='%s:30305'          > /tmp/log2 2>&1 &" % (hosts[0].IP(), hosts[1].IP())
  
  print cmd2, hosts[1].cmd(cmd2)
  print cmd1, hosts[0].cmd(cmd1)
  """  
  sleep(total_time + 5)
  exp.stop()

if __name__ == "__main__":
  simpleTest()
