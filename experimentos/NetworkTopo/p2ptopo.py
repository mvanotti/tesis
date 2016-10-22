from mininet.topo import Topo

import random
import re

def fix_mac(mac): return ':'.join([x if len(x) == 2 else "0"+x for x in mac.split(':')])

class P2P(Topo):
    def randByte(self):
        return hex(random.randint(0, 255))[2:]

    def makeMAC(self, i):
        return fix_mac("22:" + self.randByte() + ":" + \
               self.randByte() + ":00:00:" + hex(i)[2:])

    def makeDPID(self, i):
        a = self.makeMAC(i)
        dp = "".join(re.findall(r'[a-f0-9]+', a))
        return "0" * (12 - len(dp)) + dp

    def ips2nodes(self):
        res = {}
        for h in self.hosts():
            res[h.ip] = h

    def get_dpid(self, switch):
        return self.switch_to_dpid[switch]

    def build(self, nodesInfo, p2pconns, **opts):
        # conns is a dictionary, whose keys are the hosts and values is a list of tuples (h2, latency).
        # p2pconns is a set containing all the connections in string format "ip" -> "ip". If None, it will be ignored (all pairs will be connected.
        #Topo.__init__(self, **opts)
        self.switch_to_dpid = {}

        s = 1
        i = 0
        bw = 1000

        hosts = {}
        switches = {}
        for host in sorted(nodesInfo.keys()):
            i += 1
            h = self.addHost("h_%s" % host, mac=self.makeMAC(s), ip=("10.0.0.%d" % i))
            self.switch_to_dpid["s_%s" % host] = self.makeDPID(s)
            print("s_%s: %s" % (host, self.get_dpid("s_%s" % host)))
            sw = self.addSwitch("s_%s" % host, dpid=self.switch_to_dpid["s_%s" % host], **dict(listenPort=(13000 + s - 1)))
            s += 1
            self.addLink(h, sw, bw=bw)
            hosts[host] = h
            switches[host] = sw

        for host1 in sorted(nodesInfo.keys()):
            h1 = hosts[host1]
            s1 = switches[host1]
            ip1 = self.nodeInfo(h1)["ip"]
            for host2, info in nodesInfo[host1]:
                h2 = hosts[host2]
                s2 = switches[host2]
                ip2 = self.nodeInfo(h2)["ip"]

                key, keyrev = ('"%s" -> "%s"' % (ip1, ip2), '"%s" -> "%s"' % (ip2, ip1))
                if not p2pconns is None and key not in p2pconns and keyrev not in p2pconns: continue

                lat, jitter, loss = info
                print("%s <-> %s (%.2fms)" % (host1, host2, lat))
                self.addLink(s1, s2, bw=bw, delay=("%.2fms" % lat), jitter=jitter, loss=loss)