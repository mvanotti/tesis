from sys import stdin
from parser import parseMetric
from analyzer import block_propagation, propagation_statistics, block_propagation_histogram, block_generation_graph
from statistics import mean, median, stdev, variance

def main():
    """Usage: python parser.py < logfile """
    metrics = []
    nodes = set([])
    for line in stdin:
        metric = parseMetric(line)
        if metric is None: continue
        metrics.append(metric)
        nodes.add(metric["nodeID"])
    metrics = linearize(metrics)
    print("Total blocks sent: %d" % len(get_all_blocks(metrics)))

    # We need at least 10 minutes of data.
    if metrics[-1]["timestamp"] - metrics[0]["timestamp"] < 1000 * 60 * 10:
        print("Not enough data! %d" % (metrics[0]["timestamp"] - metrics[-1]["timestamp"]))
        return
    #calculateTimeDifferencesAllHosts(metrics)
    # print "var nodes = ", json.dumps(list(nodes)), ";"
    # print "var data = ", json.dumps(metrics), ";"

    block_prop_times = block_propagation(metrics)
    block_stats, unreceived = propagation_statistics(len(nodes), block_prop_times)
    print("Blocks not received by everyone: %d/%d" % (len(unreceived), len(block_prop_times)))
    for k in unreceived[:30]:
        print(k, len(block_prop_times[k]))

    for p in sorted(block_stats.keys()):
        vals = block_stats[p]
        print("Blocks propagated to %d%% of nodes in:" % p)
        if (len(vals)) < 10:
            print("Not enough data!")
            return
        print("mean: %d, median: %d, max: %d, min: %d, stddev: %d, variance: %d" %
              (mean(vals), median(vals), max(vals), min(vals), stdev(vals), variance(vals)))

    block_propagation_histogram(block_prop_times)

    block_generation_graph(metrics)

"""
    tx_prop_times = transaction_propagation(metrics)
    tx_stats, unreceived = propagation_statistics(len(nodes), tx_prop_times)
    print("Txs not received by everyone: %d/%d" % (len(unreceived), len(tx_prop_times)))

    print(unreceived[4])

    for p in sorted(tx_stats.keys()):
        vals = tx_stats[p]
        print("Txs propagated to %d%% of nodes in:" % p)
        print("mean: %d, median: %d, max: %d, min: %d, stddev: %d, variance: %d" %
              (mean(vals), median(vals), max(vals), min(vals), stdev(vals), variance(vals)))

        # block_propagation_histogram(tx_prop_times)
        # bwInfo = getBandwithUsage(metrics)
"""

def linearize(metrics):
    return sorted(metrics, key=lambda m: int(m["timestamp"]))

def get_all_blocks(metrics):
    return set([m["hash"] for m in metrics if m["event"] in ["broadcastBlock", "newBlock", "newBlockHash"]])

if __name__ == "__main__":
    main()