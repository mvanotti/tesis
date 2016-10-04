from time import sleep
from p2ptopo import P2P
from expconfig import parse_connectivity
from mininet.net import Mininet
from mininet.log import setLogLevel
from mininet.node import RemoteController
from mininet.node import OVSSwitch
from mininet.link import TCLink
from mininet.cli import CLI
import random
import re

from mininet.topo import Topo

import urllib2
import json

class SimpleTopo(Topo):
    def randByte(self):
        return hex(random.randint(0, 255))[2:]

    def makeMAC(self, i):
        return fix_mac("22:" + self.randByte() + ":" + \
               self.randByte() + ":00:00:" + hex(i)[2:])

    def makeDPID(self, i):
        a = self.makeMAC(i)
        dp = "".join(re.findall(r'[a-f0-9]+', a))
        return "0" * (12 - len(dp)) + dp

    # SimpleTopo is a topology with 2hosts and 2 switches:
    # h1 -- s1 -- s2 -- h2
    def build(self, **opts):
        switch1 = self.addSwitch('s_1', dpid=self.makeDPID(1))
        switch2 = self.addSwitch('s_2', dpid=self.makeDPID(2))

        host1 = self.addHost('h_1', mac=self.makeMAC(1), ip=("10.0.0.1"))
        host2 = self.addHost('h_2', mac=self.makeMAC(2), ip=("10.0.0.2"))

        self.addLink(switch1, switch2, bw=10, delay='1ms')
        self.addLink(host1, switch1, bw=10)
        self.addLink(host2, switch2, bw=10)

        return

def convert_dpid(dpid): return ':'.join(a+b for a,b in zip(dpid[::2], dpid[1::2]))
def fix_mac(mac): return ':'.join([x if len(x) == 2 else "0"+x for x in mac.split(':')])

def send_request(url, r):
    req = urllib2.Request(url)
    req.add_header('Content-Type', 'application/json')
    print(json.dumps(r))
    resp = urllib2.urlopen(req, json.dumps(r))
    print(resp.read())

def create_static_routing(net, topo, cinfo):
    controller_url = "http://%s:%d/wm/staticflowpusher/json" % cinfo

    h1, h2 = net.get("h_1"), net.get("h_2")
    s1, s2 = net.get("s_1"), net.get("s_2")

    h1.setARP(h2.IP(), h2.MAC())
    h2.setARP(h1.IP(), h1.MAC())

    h1s1_ports = topo.port("s_1", "h_1")
    h2s2_ports = topo.port("s_2", "h_2")
    s1s2_ports = topo.port("s_1", "s_2")

    # Everytime s1 receives a packet that is destined to h1, send it trough that port.
    request = {
        "switch": convert_dpid(s1.dpid),
        "name": "flow-%s-%s" % (s1, h1),
        "cookie": "0",
        "active": "true",
        "eth_dst": fix_mac(h1.MAC()),
        "actions": "output=%d" % (h1s1_ports[0])
    }
    send_request(controller_url, request)

    # Everytime s2 receives a packet that is destined to h2, send it trough that port.
    request["switch"] = convert_dpid(s2.dpid)
    request["name"]  = "flow-%s-%s" % (s2, h2)
    request["eth_dst"] = fix_mac(h2.MAC())
    request["actions"] = "output=%d" % (h2s2_ports[0])
    send_request(controller_url, request)

    # Everytime s1 receives a packet that is destined to h2, it should send it to s2.
    request["switch"] = convert_dpid(s1.dpid)
    request["name"] = "flow-%s-%s" % (s1, s2)
    request["eth_dst"] = fix_mac(h2.MAC())
    request["actions"] = "output=%d" % (s1s2_ports[0])
    send_request(controller_url, request)

    # Everytime s2 receives a packet that is destined to h1, it should send it to s1.
    request["switch"] = convert_dpid(s2.dpid)
    request["name"] = "flow-%s-%s" % (s2, s1)
    request["eth_dst"] = fix_mac(h1.MAC())
    request["actions"] = "output=%d" % (s1s2_ports[1])
    send_request(controller_url, request)

def simpleTest():
    topo = SimpleTopo()

    controller_ip = '127.0.0.1'
    controller_port = 6633

    net = Mininet(topo, controller=lambda name: RemoteController( name, ip=controller_ip, port=controller_port), switch=OVSSwitch, link=TCLink)
    #net = Mininet(topo, switch=OVSSwitch, link=TCLink)
    net.start()

    print("Waiting for Networking Algorithms to converge")
    sleep(10 * 1)
    create_static_routing(net, topo, (controller_ip, 8080))
    sleep(3 * 1)

    net.pingAllFull()
    h1, h2 = net.hosts[0], net.hosts[1]

    h1.cmd("timeout 20 iperf -s &")
    sleep(5)
    h2.cmdPrint("iperf -c %s" % h1.IP())

    CLI(net)

    net.stop()

if __name__ == "__main__":
    setLogLevel('info')
    simpleTest()
