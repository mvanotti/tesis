import json
from sys import stdin
from collections import Counter


def main():
    data = json.load(stdin)
    total_nodes = int(data["total_nodes"])
    nodes = data["nodes"]
    print("Total Nodes: %d, nodes: %d" % (total_nodes, len(nodes)))
    countries = sorted([v[7] for v in nodes.values() if len(v) > 7 and len(str(v[7])) == 2])
    countries = Counter(countries)
    for c, n in countries.most_common():
        print("%s %d" % (c, n))


if __name__ == "__main__":
    main()