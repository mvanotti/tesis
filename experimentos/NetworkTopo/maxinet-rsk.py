from time import sleep
from expconfig import parse_connectivity
from p2ptopo import P2P

from MaxiNet.Frontend import maxinet
from MaxiNet.tools import Tools
from mininet.node import OVSSwitch
from mininet.link import TCLink
from mininet.node import RemoteController

import random
import pickle

def simpleTest():
    total_time = 60 * 60 * 3
    with open("topo.pickle", "r") as f:
        conns = pickle.load(f)

    p2pconns = parse_connectivity("/home/maxinet/rsk/configs/connectivity.dot")
    topo = P2P(conns, p2pconns)

    cluster = maxinet.Cluster()
    exp = maxinet.Experiment(cluster, topo, switch=OVSSwitch)
    exp.setup()

    hosts = exp.hosts
    print("waiting for routing algorithms on te controller to converge")
    sleep(60 * 30)
    print("Starting experiment!!")

    for host1, host2 in topo.links():
        # We only care about inter-switch communcations, because two nodes are connected if their switches are connected.
        if not host1.startswith("s-") or not host2.startswith("s-"): continue
        host1 = host1.replace("s-", "h-")
        host2 = host2.replace("s-", "h-")
        h1, h2 = exp.get_node(host1), exp.get_node(host2)
        print(h1.cmd("ping -c 2 -w 1 %s " % h2.IP()))

    sleep(60 * 30)

    for duration in [10, 8, 6, 4, 2]:
        cmd = {}
        for i in range(len(hosts)):
            h = hosts[i]
            c = """timeout %d /home/maxinet/rsk/jdk1.8/jre/bin/java -jar\
                -Dethereumj.conf.file=/home/maxinet/rsk/configs/node%s.conf-%d \
                -Dlog4j.configuration=file:/home/maxinet/rsk/logsconfigs/log4j.properties.%s \
                /home/maxinet/rsk/ethereumj-core-0.0.1-LOTUS-all.jar > /usr/tmp/%s-logs-%d 2>&1 &""" % (total_time, str(h.IP()), duration, str(h.IP()), str(h.IP()), duration)
            cmd[h.name] = c
        for h in hosts:
            print(cmd[h.name], h.cmd(cmd[h.name]))
        sleep(total_time + 60 * 5)

    exp.stop()

if __name__ == "__main__":
    simpleTest()
