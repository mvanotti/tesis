from sys import stdin
from itertools import groupby
from statistics import mean, median, stdev, variance
import json
import time

current_milli_time = lambda: int(round(time.time() * 1000))


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


def blockPropagation(metrics):
    blocks = {}
    for m in filter(lambda m: m["event"] in ["broadcastBlock", "newBlock"], metrics):
        hash = m["hash"]
        if hash not in blocks:
            blocks[hash] = []
        blocks[hash].append(m)

    propagationTimes = {}
    for hash, ls in blocks.iteritems():
        visited = set([])  # Only count the first time a node receives a block.
        startTime = ls[0]["timestamp"]

        # times is a list of (elapsedTime, node).
        # for each node, how long did it take to receive the block.
        times = []
        for m in ls:
            node = m["nodeID"]
            if node in visited: continue
            visited.add(node)

            elapsed = m["timestamp"] - startTime
            times.append((elapsed, node))

        propagationTimes[hash] = times
    return propagationTimes


def txPropagation(metrics):
    blocks = {}
    for m in filter(lambda m: m["event"] in ["broadcastTransaction", "newTransaction"], metrics):
        hash = m["hash"]
        if hash not in blocks:
            blocks[hash] = []
        blocks[hash].append(m)

    propagationTimes = {}
    for hash, ls in blocks.iteritems():
        visited = set([])  # Only count the first time a node receives a block.
        startTime = ls[0]["timestamp"]

        # times is a list of (elapsedTime, node).
        # for each node, how long did it take to receive the block.
        times = []
        for m in ls:
            node = m["nodeID"]
            if node in visited: continue
            visited.add(node)

            elapsed = m["timestamp"] - startTime
            times.append((elapsed, node))

        propagationTimes[hash] = times
    return propagationTimes


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

def main():
    """Usage: python parser.py < logfile """
    metrics = []
    nodes = set([])
    for line in stdin:
        metric = parseMetric(line)
        if metric is None: continue
        metrics.append(metric)

    metrics = linearize(metrics)
    #calculateTimeDifferencesAllHosts(metrics)
    # print "var nodes = ", json.dumps(list(nodes)), ";"
    # print "var data = ", json.dumps(metrics), ";"
    # propTimes = blockPropagation(metrics)
    # for hash, times in propTimes.iteritems():
    # print "Block %s propagated in %d" % (hash, times[-1][0])

    # txTimes = txPropagation(metrics)
    # for hash, times in txTimes.iteritems():
    # print "Tx %s propagated in %d" % (hash, times[-1][0])

    # bwInfo = getBandwithUsage(metrics)


if __name__ == "__main__":
    main()
