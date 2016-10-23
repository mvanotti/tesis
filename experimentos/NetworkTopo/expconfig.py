import pickle

def parse_connectivity(file):
    with open(file, "r") as f:
        content = [l.strip() for l in f.readlines() if "->" in l]
    return set(content)

def create_connectivity_dict(conns):
    res = {}
    for conn in conns:
        ls = conn.split("->")
        a = ls[0].strip().replace("\"", "")
        b = ls[1].strip().replace("\"", "")
        if a not in res:
            res[a] = set()
        if b not in res:
            res[b] = set()
        res[b].add(a)
        res[a].add(b)
    return res

def create_simgrid_files(hostsInfo, nodesInfo):
    # nodesInfo has, for each node in the system, its peers.
    # hostsInfo has, for each host in the network, it's latency to the rest of the hosts.

    host2node = {}
    node2host = {}
    hostsnodes = zip(sorted(hostsInfo.keys()), sorted(nodesInfo.keys()))
    for h, n in hostsnodes:
        print(h, n)
        host2node[h] = n
        node2host[n] = h

    xml_preamble = \
    """<?xml version='1.0'?>
    <!DOCTYPE platform SYSTEM "http://simgrid.gforge.inria.fr/simgrid/simgrid.dtd">
    <platform version="4">
      <AS  id="AS0"  routing="Full">
    """

    xml_end = \
    """
      </AS>
    </platform>
    """

    xml_hosts = ['\t<host id="%s" speed="100.0Mf" core="3"/>' % h for h in sorted(hostsInfo.keys())]

    xml_links = ['\t<link id="loopback" latency="0ms" bandwidth="10000MBps" />']
    xml_routes = []
    for h in hostsInfo.keys():
        n = host2node[h]

        xml_route = "\n".join(['\t<route src="%s" dst="%s">' % (h, h),
                                    '\t\t<link_ctn id="%s"/>' % ("loopback"),
                                    '\t</route>'])
        xml_routes.append(xml_route)
        for (p, info) in hostsInfo[h]:
            np = host2node[p]
            if np not in nodesInfo[n]: continue

            lat, jitter, loss = info
            link_id = "%s-%s" % (h, p)
            xml_link = '\t<link id="%s" latency="%fms" bandwidth="100MBps" />' % (link_id, lat)
            xml_links.append(xml_link)

            xml_route = "\n".join(['\t<route src="%s" dst="%s">' % (h, p),
                                    '\t\t<link_ctn id="%s"/>' % (link_id),
                                    '\t</route>'])
            xml_routes.append(xml_route)


    xml_hosts = '\n'.join(xml_hosts)
    xml_links = '\n'.join(xml_links)
    xml_routes = '\n'.join(xml_routes)

    platform_file = '\n\n'.join([xml_preamble, xml_hosts, xml_links, xml_routes, xml_end])

    xml_preamble = \
    """<?xml version='1.0'?>
    <!DOCTYPE platform SYSTEM "http://simgrid.gforge.inria.fr/simgrid/simgrid.dtd">
    <platform version="4">
    """
    xml_end = "</platform>"

    xml_processes = []
    for h in hostsInfo.keys():
        xml_process = ['\t<process host="%s" function="io.rootstock.simgrid.RSKNode">' % h]
        n = host2node[h]
        for np in nodesInfo[n]:
            p = node2host[np]
            xml_process.append('\t\t<argument value="%s" />' % p)

        xml_process.append('\t</process>')
        xml_processes.append('\n'.join(xml_process))

    xml_processes = '\n'.join(xml_processes)

    deployment_file = '\n'.join([xml_preamble, xml_processes, xml_end])
    return platform_file, deployment_file


if __name__ == "__main__":
    with open("topo.pickle", "rb") as f:
        conns = pickle.load(f)

    p2pconns = create_connectivity_dict(parse_connectivity("connectivity.dot"))

    print(len(conns), len(p2pconns))
    platform, deployment = create_simgrid_files(conns, p2pconns)

    with open("/tmp/deployment.xml", "w") as f:
        f.write(deployment)

    with open("/tmp/platform.xml", "w") as f:
        f.write(platform)
