from time import sleep
from p2ptopo import P2P
from expconfig import parse_connectivity
from mininet.net import Mininet
from mininet.log import setLogLevel
from mininet.node import RemoteController
from mininet.node import OVSSwitch
from mininet.link import TCLink
from staticrouting import create_static_routing
from mininet.cli import CLI

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
        print("%s -> %s" % (a, b))
        res[a].add(b)
    return res

def listen_everyone(hosts, conns):
    for h in hosts:
        h.cmdPrint("iperf -s 2>&1 > /tmp/%s &" % h.IP())
        # Levantar servidor.
    sleep(5)
    for k in conns.keys():
        print(k)
        h = ip2host[k]
        for ip in conns[k]:
            h.cmdPrint("iperf -c %s -n 10M -x CDMSV 2>&1" % ip)

def simpleTest():
    total_time = 120
    with open("topo.pickle", "r") as f:
        conns = pickle.load(f)
    #print(conns)
    p2pconns = parse_connectivity("/home/mvanotti/connectivity.dot")
    topo = P2P(conns, p2pconns)

    net = Mininet(topo, controller=lambda name: RemoteController( name, ip='127.0.0.1',port=6633 ), switch=OVSSwitch, link=TCLink)
    net.start()

    hosts = net.hosts
    for h in hosts:
        ip2host[h.IP()] = h

    print("Waiting for Networking Algorithms to converge")
    sleep(10 * 1)
    create_static_routing(net, topo, ("127.0.0.1", 8080) )
    sleep(10 * 1)

    conns = create_connectivity_dict(p2pconns)
    listen_everyone(hosts, conns)

    sleep(total_time)
    net.stop()

if __name__ == "__main__":
    setLogLevel('info')
    simpleTest()
