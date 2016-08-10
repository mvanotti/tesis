from sys import stdin
from statistics import mean, median, stdev, variance
import numpy as np
import matplotlib.mlab as mlab
import matplotlib.pyplot as plt
import time

def current_milli_time():
    return int(round(time.time() * 1000))

def parseMessageBytes(metric):
    return {
        "event": metric[1],
        "bytes": metric[3],
        "sender": metric[5],
    }


def parseNewBlock(metric):
    return {
        "event": metric[1],
        "hash": metric[3],
        "number": int(metric[5]),
        "parent": metric[7],
        "sender": metric[9],
    }


def parseNewTransaction(metric):
    return {
        "event": metric[1],
        "hash": metric[3],
        "nonce": int(metric[5]),
        "sender": metric[7],
    }


def parseBroadcastBlock(metric):
    return {
        "event": metric[1],
        "hash": metric[3],
        "number": int(metric[5]),
        "parent": metric[7],
    }


def parseBroadcastTransaction(metric):
    return {
        "event": metric[1],
        "hash": metric[3],
        "nonce": int(metric[5]),
    }


def parseNewBlockHash(metric):
    return {
        "event": metric[1],
        "hash": metric[3],
        "number": int(metric[5]),
        "sender": metric[7],
    }


def parseNewBlockHeader(metric):
    return {
        "event": metric[1],
        "hash": metric[3],
        "number": int(metric[5]),
        "parent": metric[7],
        "sender": metric[9],
    }


def parseEventWithHash(metric):
    return {
        "nodeID": metric[4],
        "event": metric[6],
        "hash": metric[7],
        "timestamp": int(metric[9]),
        "nano": int(metric[11])
    }


metricsParser = {
    "messageBytes": parseMessageBytes,
    "newBlock": parseNewBlock,
    "newTransaction": parseNewTransaction,
    "broadcastTransaction": parseBroadcastTransaction,
    "broadcastBlock": parseBroadcastBlock,
    "newBlockHeader": parseNewBlockHeader,
    "newBlockHash": parseNewBlockHash,
}


def linearize(metrics):
    return sorted(metrics, key=lambda m: int(m["timestamp"]))


def block_propagation(metrics):
    blocks = {}
    for m in filter(lambda m: m["event"] in ["broadcastBlock", "newBlock"], metrics):
        hash = m["hash"]
        if hash not in blocks:
            blocks[hash] = []
        blocks[hash].append(m)

    propagation_times = {}
    for hash, ls in blocks.items():
        visited = set([])  # Only count the first time a node receives a block.
        start_time = ls[0]["timestamp"]
        if ls[0]["event"] != "broadcastBlock":
            print("Block with hash %s received appeared out of order!" % ls[0]["hash"])
            continue

        # times is a list of (elapsedTime, node).
        # for each node, how long did it take to receive the block.
        times = [(0, ls[0]["nodeID"])]
        ls = [m for m in ls if m["event"] == "newBlock"]
        for m in ls:
            node = m["nodeID"]
            if node in visited: continue
            visited.add(node)

            elapsed = m["timestamp"] - start_time
            times.append((elapsed, node))

        propagation_times[(hash,start_time)] = times
    return propagation_times


def transaction_propagation(metrics):
    txs = {}
    for m in filter(lambda m: m["event"] in ["broadcastTransaction", "newTransaction"], metrics):
        hash = m["hash"]
        if hash not in txs:
            txs[hash] = []
        txs[hash].append(m)

    propagation_times = {}
    for hash, ls in txs.items():
        visited = set([])  # Only count the first time a node receives a tx.
        start_time = ls[0]["timestamp"]
        if ls[0]["event"] != "broadcastTransaction":
            print("Transaction with hash %s received appeared out of order!" % ls[0]["hash"])
            continue

        # times is a list of (elapsedTime, node).
        # for each node, how long did it take to receive the block.
        times = [(0, ls[0]["nodeID"])]
        ls = [m for m in ls if m["event"] == "newTransaction"]
        for m in ls:
            node = m["nodeID"]
            if node in visited: continue
            visited.add(node)

            elapsed = m["timestamp"] - start_time
            times.append((elapsed, node))

        propagation_times[(hash, start_time)] = times
    return propagation_times


def getBandwithUsage(metrics):
    return 0


def parseMetric(line):
    # Example: 17:52:05.322 INFO [metrics]  950a92 at: 1468270325320 nano: 36267820527878 | event: broadcastBlock hash: 6acea6 number: 1 parent: a7f584
    metric = line.strip().split(' ')
    if len(metric) < 12: return None
    nodeID = metric[4]
    timestamp = metric[6]
    nano = metric[8]
    event = metric[11]

    if event not in metricsParser: return None

    metric = metricsParser[event](metric[10:])
    metric["nodeID"] = nodeID
    metric["timestamp"] = int(timestamp)
    metric["nano"] = int(nano)
    return metric

def calculateTimeDifferences(host_metrics):
    """ calculateTimeDifferences will print the statistics about the time differences for the metrics for this host.
        It calculates the difference in wall-clock time from one metric to the next, and the difference in app time,
        and get the absolute value of the difference. This value would be the time drift that happened
        because NTP synchronization. """
    deltas = []
    print("Host: %s" % host_metrics[0]["nodeID"])
    for i in range(len(host_metrics) - 1):
        deltaTimeMillis = host_metrics[i+1]["timestamp"] - host_metrics[i]["timestamp"]
        deltaTimeNanos  = host_metrics[i+1]["nano"] - host_metrics[i]["nano"]

        deltasDifference = abs(deltaTimeMillis - deltaTimeNanos/1000000.0)
        if deltasDifference > 100000:
           print(deltasDifference, host_metrics[i], host_metrics[i+1])
        deltas.append(deltasDifference)
    if len(deltas) < 2:
        print("No Data")
        return

    print("Metrics: %d, Mean: %.4f, Median: %.4f, Max: %.4f, Std: %.4f, Variance: %.4f" %
          (len(deltas), mean(deltas), median(deltas), max(deltas), stdev(deltas), variance(deltas)))


def calculateTimeDifferencesAllHosts(metrics):
    """calculateTimeDifferencesAllHosts will estimate the time-drifting for each host in the network. """
    hostsMetrics = metricsByHost(metrics)

    for h in sorted(hostsMetrics.keys()):
        calculateTimeDifferences(hostsMetrics[h])
    return None

def metricsByHost(metrics):
    """metricsByHost will split the metrics for each different host. """
    hostfunc = lambda x: x["nodeID"]
    res = {}
    for m in metrics:
        k = m["nodeID"]
        if k not in res:
            res[k] = []
        res[k].append(m)

    return res

def propagation_statistics(nodes, prop_times):
    unreceived = []
    percentages = {10:[], 50:[], 90:[], 100:[]}
    indexes = [ min(int(x * nodes / 100.0), nodes - 1) for x in sorted(percentages.keys())]
    for hash, times in prop_times.items():
        if len(times) < nodes:
            #print(hash, len(times))
            unreceived.append(hash)
            continue
        proptimes = [times[i][0] for i in indexes]
        percentages[10].append(proptimes[0])
        percentages[50].append(proptimes[1])
        percentages[90].append(proptimes[2])
        percentages[100].append(proptimes[3])

    return percentages, unreceived

def block_propagation_histogram(prop_times):
    data = []
    for h, times in prop_times.items():
        data += [min(t[0]/1000.0, 10.0) for t in times]

    # the histogram of the data
        bins = [x/2 for x in range(0, 21)]
    print(bins)
    n, bins, patches = plt.hist(data, bins=bins, facecolor='g', alpha=0.75, weights=100*(np.zeros_like(data) + 1. / len(data)), cumulative=True)

    plt.xlabel('Seconds')
    plt.ylabel('cumulative % of Blocks Received')
    plt.title('Histogram of Block Propagation Times (cumulative)')
    plt.grid(True)
    plt.savefig(filename="/tmp/cumulative.png")
    plt.clf()
    n, bins, patches = plt.hist(data, bins=bins, facecolor='g', alpha=0.75, weights=100*(np.zeros_like(data) + 1. / len(data)), cumulative=False)
    plt.xlabel('Seconds')
    plt.ylabel('% of Blocks Received')
    plt.title('Histogram of Block Propagation Times')
    plt.grid(True)
    plt.savefig(filename="/tmp/noncumulative.png")
    plt.clf()



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
    #calculateTimeDifferencesAllHosts(metrics)
    # print "var nodes = ", json.dumps(list(nodes)), ";"
    # print "var data = ", json.dumps(metrics), ";"

    block_prop_times = block_propagation(metrics)
    block_stats, unreceived = propagation_statistics(len(nodes), block_prop_times)
    print("Blocks not received by everyone: %d/%d" % (len(unreceived), len(block_prop_times)))
    for k in unreceived[20:30]:
        print(k, len(block_prop_times[k]))

    for p in sorted(block_stats.keys()):
        vals = block_stats[p]
        print("Blocks propagated to %d%% of nodes in:" % p)
        print("mean: %d, median: %d, max: %d, min: %d, stddev: %d, variance: %d" %
              (mean(vals), median(vals), max(vals), min(vals), stdev(vals), variance(vals)))

    block_propagation_histogram(block_prop_times)


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


if __name__ == "__main__":
    main()
