from time import sleep
from mininet.topo import Topo
from mininet.net import Mininet
from mininet.log import setLogLevel
from mininet.node import RemoteController
from mininet.node import OVSSwitch
from mininet.link import TCLink

from networktopo import parse_topo, parse_latencies, pick_random_topo

import random
import re


class P2P(Topo):
    def randByte(self):
        return hex(random.randint(0, 255))[2:]

    def makeMAC(self, i):
        return self.randByte() + ":" + self.randByte() + ":" + \
               self.randByte() + ":00:00:" + hex(i)[2:]

    def makeDPID(self, i):
        a = self.makeMAC(i)
        dp = "".join(re.findall(r'[a-f0-9]+', a))
        return "0" * (12 - len(dp)) + dp

    def __init__(self, conns, **opts):
        # conns is a dictionary, whose keys are the hosts and values is a list of tuples (h2, latency).

        Topo.__init__(self, **opts)

        s = 1
        i = 0
        bw = 10

        hosts = {}
        switches = {}
        for host in sorted(conns.keys()):
            i+=1
            h = self.addHost("h-%s" % host, mac=self.makeMAC(i), ip=("10.0.0.%d" % i))
            sw = self.addSwitch("s-%s" % host, dpid=self.makeDPID(s), **dict(listenPort=(13000 + s - 1)))
            s += 1
            self.addLink(h, sw, bw=bw, delay="0.1ms")
            hosts[host] = h
            switches[host] = sw

        for host1 in sorted(conns.keys()):
            for host2, lat in conns[host1]:
                print("%s <-> %s (%.2fms)" % (host1, host2, lat))
                self.addLink(switches[host1], switches[host2], bw=bw, delay=("%.2fms" % lat))

def make_conns(n):
    res = {}
    for i in range(n):
        host = "%d" % i
        res[host] = [("%d" % j, 1) for j in range(i)]
    return res

def simpleTest():
    "Create and test a simple network"
    total_time = 60
    countries = parse_topo("country-distribution.csv")
    latencies = parse_latencies("topology.graphml.xml")
    conns = pick_random_topo(countries, latencies, 32)
    print(conns)
    topo = P2P(conns)
    net = Mininet(topo, controller=lambda name: RemoteController( name, ip='127.0.0.1',port=6633 ), switch=OVSSwitch, link=TCLink)
    net.start()

    hosts = net.hosts
    print(hosts)
    with open("peers", "w") as f:
        for h in hosts:
            print("Host %s has ip %s" % (h.name, h.IP()))
            f.write("%s:%d\n" % (h.IP(), 5020))

    print("Waiting for Networking Algorithms to converge")
    sleep(60*5)
    print("holi")
    net.pingAllFull()
    sleep(60 * 5)
    net.pingAllFull()
    sleep(60 * 5)
    cmd = {}
    for i in range(len(hosts)):
        c = """timeout %d /home/mininet/networktest/node -h %d > /tmp/pruebas/%d.test 2>&1 &""" % (total_time, i, i)
        cmd[hosts[i].name] = c

    for h in hosts:
        if h.name not in cmd: continue
        print(cmd[h.name], h.cmd(cmd[h.name]))

    sleep(total_time + 60)
    net.stop()

if __name__ == "__main__":
    setLogLevel('info')
    simpleTest()
