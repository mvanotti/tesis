from time import sleep

from MaxiNet.Frontend import maxinet
from mininet.topo import Topo
from MaxiNet.tools import FatTree
from MaxiNet.tools import Tools
from mininet.node import OVSSwitch


def simpleTest():
  "Create and test a simple network"
  total_time = 60 * 60
  max_nodes_per_worker = 3
  n = 50
  topo = FatTree(n, 10, 1)

  cluster = maxinet.Cluster()

  exp = maxinet.Experiment(cluster, topo, switch=OVSSwitch)
  exp.setup()
  print("Hostname mapping:", exp.generate_hostname_mapping())
  hosts = [exp.get_node("h%d" % i) for i in range(1, n+1)]
  workers = {}
  for h in hosts:
    worker = exp.get_worker(h).hn()
    print("For host ", h.name, " Worker is ", worker)
    if not worker in workers:
      workers[worker] = []
    workers[worker].append(h.IP())
  # En workers tenemos, para cada worker, la cantidad de hosts que hay.

  for h in hosts:
    print("Host %s has ip %s" % (h.name, h.IP()))

  print("waiting 10 seconds for routing algorithms on te controller to converge")
  sleep(10)
  print("Starting experiment!!")

  cmd = {}
  for h in hosts:
    c = """timeout %d /home/maxinet/rsk/rsk/jdk1.8/jre/bin/java -jar\
                    -Dethereumj.conf.file=/home/maxinet/rsk/configs/node%s.conf \
                    -Dlog4j.configuration=file:/home/maxinet/rsk/logsconfigs/log4j.properties.%s \
                    /home/maxinet/rsk/rsk/ethereumj-core-0.0.1-LOTUS-all.jar > /usr/tmp/%s-logs 2>&1 &""" % (total_time, str(h.IP()), str(h.IP()), str(h.IP()))
    cmd[h.name] = c
    
  for h in hosts:
    print(cmd[h.name], h.cmd(cmd[h.name]))

  sleep(total_time + 60)
  exp.stop()

if __name__ == "__main__":
  simpleTest()
