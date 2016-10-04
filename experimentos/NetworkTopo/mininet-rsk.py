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

def simpleTest():
    total_time = 60 * 60 * 24
    with open("topo.pickle", "r") as f:
        conns = pickle.load(f)
    #print(conns)
    p2pconns = parse_connectivity("/home/mvanotti/rsk/configs/connectivity.dot")
    topo = P2P(conns, p2pconns)

    net = Mininet(topo, controller=lambda name: RemoteController( name, ip='127.0.0.1',port=6633 ), switch=OVSSwitch, link=TCLink)
    net.start()

    hosts = net.hosts

    print("Waiting for Networking Algorithms to converge")
    sleep(10 * 1)
    create_static_routing(net, topo, ("127.0.0.1", 8080) )
    sleep(10 * 1)
    #net.pingAllFull()

    cmd = {}
    for i in range(len(hosts)):
        h = hosts[i]
        c = """timeout %d java -jar \
            -Dethereumj.conf.file=/home/mvanotti/rsk/configs/node%s.conf \
            -Dlog4j.configuration=file:/home/mvanotti/rsk/logsconfigs/log4j.properties.%s \
            /home/mvanotti/rsk/ethereumj-core-0.0.1-LOTUS-all.jar > /home/mvanotti/rsk/logs/%s-logs 2>&1 &""" % (total_time, str(h.IP()), str(h.IP()), str(h.IP()))
        cmd[hosts[i].name] = c


    for h in hosts:
        if h.name not in cmd: continue
        print(cmd[h.name], h.cmd(cmd[h.name]))

    sleep(total_time + 60)
    net.stop()

if __name__ == "__main__":
    setLogLevel('info')
    simpleTest()
