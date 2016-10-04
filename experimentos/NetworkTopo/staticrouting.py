from time import sleep
from p2ptopo import P2P
from expconfig import parse_connectivity
from mininet.net import Mininet
from mininet.log import setLogLevel
from mininet.node import RemoteController
from mininet.node import OVSSwitch
from mininet.link import TCLink
from mininet.cli import CLI

import urllib2
import json
import pickle

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
    # Things to do:
    # h1 -- s1 -- s2 -- h2
    # s1 needs a flow to h1 if h1 is in the dst mac address.
    # s2 needs a flow to h2 if h2 is in the dst mac address.
    #
    # if there is a link between s1 and s2:
    #   s1 needs a flow to s2 port if dst mac address is h2.macaddress
    #   s2 needs a flow to s1 port if dst mac address is h1.macaddress
    #
    # create ARP tables for each host.
    hosts = net.hosts
    for i in range(len(hosts)):
        h1 = hosts[i]
        for j in range(len(hosts)):
            h2 = hosts[j]
            h1.setARP(h2.IP(), h2.MAC())

    for s in topo.switches():
        h = s.replace("s_", "h_")
        host, switch = net.get(h), net.get(s)
        if not switch.connected(): print("Not connected! %s" % s)
        pn = topo.port(s, h)

        request = {
                    "switch": convert_dpid(switch.dpid),
                    "name": "flow-%s-%s" % (s, h),
                    "cookie": "0",
                    "active": "true",
                    "eth_dst": fix_mac(host.MAC()),
                    "actions": "output=%d" % (pn[0])
                    }
        send_request(controller_url, request)

    for s1, s2 in topo.links():
        # We only care about inter-switch communcations, because two nodes are connected if their switches are connected.
        if not s1.startswith("s_") or not s2.startswith("s_"): continue
        h1, h2 = s1.replace("s_", "h_"), s2.replace("s_", "h_")

        switch1, switch2 = net.get(s1), net.get(s2)
        host1, host2 = net.get(h1), net.get(h2)

        pn = topo.port(s1, s2)
        ph1 = topo.port(s1, h1)
        ph2 = topo.port(s2, h2)

        request = {
            "switch": convert_dpid(switch1.dpid),
            "name": "flow-%s-%s" % (s1, s2),
            "cookie": "0",
            "active": "true",
            "eth_dst": fix_mac(host2.MAC()),
            "actions": "output=%d" % (pn[0])
        }
        send_request(controller_url, request)

        request = {
            "switch": convert_dpid(switch2.dpid),
            "name": "flow-%s-%s" % (s2, s1),
            "cookie": "0",
            "active": "true",
            "eth_dst": fix_mac(host1.MAC()),
            "actions": "output=%d" % (pn[1])
        }
        send_request(controller_url, request)

def simpleTest():
    with open("topo.pickle", "r") as f:
        conns = pickle.load(f)
    print(conns)
    topo = P2P(conns, None)

    controller_ip = '127.0.0.1'
    controller_port = 6633

    net = Mininet(topo, controller=lambda name: RemoteController( name, ip=controller_ip, port=controller_port), switch=OVSSwitch, link=TCLink)
    net.start()

    print("Waiting for Networking Algorithms to converge")
    sleep(10 * 1)
    create_static_routing(net, topo, (controller_ip, 8080))
    sleep(10 * 1)

    net.pingAllFull()

    net.stop()

if __name__ == "__main__":
    setLogLevel('info')
    simpleTest()
