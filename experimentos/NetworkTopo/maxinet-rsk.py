from time import sleep
from expconfig import parse_connectivity
from p2ptopo import P2P

from MaxiNet.Frontend import maxinet
from MaxiNet.tools import Tools
from mininet.node import OVSSwitch
from mininet.link import TCLink
from mininet.node import RemoteController
from staticrouting import create_static_routing

import random
import pickle

ip2host = {}

def create_connectivity_dict(conns):
    res = {}
    for conn in conns:
        ls = conn.split("->")
        a = ls[0].strip().replace("\"", "")
        b = ls[1].strip().replace("\"", "")
        if a not in res:
            res[a] = set()
        res[a].add(b)
    return res

def listen_everyone(hosts, conns):
    for h in hosts:
        h.cmd("iperf -s 2>&1 > /tmp/%s &" % h.IP())
        # Levantar servidor.
    sleep(5)
    for k in conns.keys():
        print(k)
        h = ip2host[k]
        for ip in conns[k]:
            print(h.cmd("iperf -c %s -n 20M 2>&1" % ip))

def simpleTest():
    total_time = 60 * 60 * 14
    with open("topo.pickle", "r") as f:
        conns = pickle.load(f)

    p2pconns = parse_connectivity("/home/maxinet/rsk/configs/connectivity.dot")
    topo = P2P(conns, p2pconns)

    cluster = maxinet.Cluster()
    exp = maxinet.Experiment(cluster, topo, switch=OVSSwitch)
    exp.setup()

    print("Waiting for switches to connect")
    sleep(10)
    for s in exp.switches:
        i = 0
        while not s.connected():
            sleep(10)
            i += 1
            if i > 10:
                print("Waited too long for switch %s" % s.name)
                break
    create_static_routing(exp, topo, ("localhost", 8080))

    hosts = exp.hosts
    print("Starting experiment!!")
    sleep(30)

    for h in hosts:
        ip2host[h.IP()] = h

    #conns = create_connectivity_dict(p2pconns)
    #listen_everyone(hosts, conns)

    #sleep(total_time)

    # for host1, host2 in topo.links():
    #     # We only care about inter-switch communcations, because two nodes are connected if their switches are connected.
    #     if not host1.startswith("s_") or not host2.startswith("s_"): continue
    #     host1 = host1.replace("s_", "h_")
    #     host2 = host2.replace("s_", "h_")
    #     h1, h2 = exp.get_node(host1), exp.get_node(host2)
    #     print(h1.cmd("ping -c 5 -W 1 %s " % h2.IP()))

    cmd = {}
    for i in range(len(hosts)):
        h = hosts[i]
        c = """timeout %d /home/maxinet/rsk/jdk1.8/jre/bin/java -jar\
            -Dethereumj.conf.file=/home/maxinet/rsk/configs/node%s.conf \
            -Dlog4j.configuration=file:/home/maxinet/rsk/logsconfigs/log4j.properties.%s \
            /home/maxinet/rsk/binary.jar > /usr/tmp/%s-logs 2>&1 &""" % (total_time, str(h.IP()), str(h.IP()), str(h.IP()))
        cmd[h.name] = c
    for h in hosts:
        print(cmd[h.name], h.cmd(cmd[h.name]))
    sleep(total_time + 60 * 5)

    exp.stop()

if __name__ == "__main__":
    simpleTest()
