import csv
from collections import Counter
from random import sample
import pickle

import xml.etree.ElementTree
import argparse


def parse_elem(e):
    return {
        "d0": lambda e: ("packetloss", float(e.text)),
        "d1": lambda e: ("ip", e.text),
        "d2": lambda e: ("geocode", e.text),
        "d3": lambda e: ("bandwidthdown", int(e.text)),
        "d4": lambda e: ("bandwidthup", int(e.text)),
        "d5": lambda e: ("type", e.text),
        "d6": lambda e: ("asn", int(e.text)),
        "d7": lambda e: ("latency", float(e.text)),
        "d8": lambda e: ("jitter", float(e.text)),
        "d9": lambda e: ("packetloss", float(e.text))
    }[e.attrib["key"]](e)

def parse_latencies(filepath):
    e = xml.etree.ElementTree.parse(filepath).getroot()
    e = e[10]
    nodes = {}
    codes = {}
    edges = []
    neighbors = {}
    for elem in e:
        if elem.tag == '{http://graphml.graphdrawing.org/xmlns}node':
            id = elem.attrib["id"]
            vals = {"id": id}
            for e in elem:
                k, v = parse_elem(e)
                vals[k] = v
                if k == "geocode":
                    code = v
            codes[id] = code
            nodes[code] = vals
        if elem.tag == '{http://graphml.graphdrawing.org/xmlns}edge':
            src, dst = elem.attrib["source"], elem.attrib["target"]
            vals = {"src": src, "dst": dst}
            for e in elem:
                k, v = parse_elem(e)
                vals[k] = v
            edges.append(vals)
    for e in edges:
        srcc = codes[e["src"]]
        dstc = codes[e["dst"]]
        if srcc not in neighbors:
            neighbors[srcc] = {}
        if dstc not in neighbors:
            neighbors[dstc] = {}

        neighbors[srcc][dstc] = (e["latency"], e["jitter"], e["packetloss"])
        neighbors[dstc][srcc] = (e["latency"], e["jitter"], e["packetloss"])

    return neighbors

def parse_topo(filepath):
    res = {}
    with open(filepath, 'r') as csvfile:
        reader = csv.reader(csvfile, delimiter=",")
        for row in reader:
            res[row[0]] = int(row[1])
    return res

def countries_sample(countries, amount):
    cnt = Counter(countries)
    population = list(cnt.elements())
    return sorted(sample(population, amount))

def pick_random_topo(countries, latencies, amount):
    nodes = countries_sample(countries, amount)
    topo = {}
    i = 0
    for i in range(len(nodes)):
        node1 = nodes[i]
        h1 = "%d-%s" % (i, node1)
        if h1 not in topo: topo[h1] = []
        if not node1 in latencies:
            print("Error! Node1 %s not recognized!" % node1)
        for j in range(i + 1, len(nodes)):
            node2 = nodes[j]
            h2 = "%d-%s" % (j, node2)
            if not node2 in latencies:
                print("Error! Node2 %s not recognized!" % node2)
            if not node2 in latencies[node1]:
                print("Error! Node2 %s not in latencies[%s]!" % (node2, node1))
            lat = latencies[node1][node2]
            topo[h1].append((h2, lat))
    return topo

def main():
    parser = argparse.ArgumentParser(description='Generate network topologies.')
    parser.add_argument('--n', dest="n", type=int, default=32, help="Number of nodes to use")
    parser.add_argument('--topofile', dest="topofile", type=str, default="topo.pickle", help="File in which to store the topology.")
    args = parser.parse_args()

    countries = parse_topo("country-distribution.csv")
    latencies = parse_latencies("topology.plab.graphml.xml")
    latencies2 = parse_latencies("topology.graphml.xml")
    topo = pick_random_topo(countries, latencies, args.n)
    topo2 = pick_random_topo(countries, latencies, args.n)

    lats = [x[1][0] for k in topo.keys() for x in topo[k]]
    lats2 = [x[1][0] for k in topo2.keys() for x in topo2[k]]

    print("Topo1: %.4f" % (sum(lats)/len(lats)))
    print("Topo2: %.4f" % (sum(lats2)/len(lats2)))

    with open(args.topofile, "w") as f:
        pickle.dump(topo, f)

if __name__ == "__main__":
    main()
