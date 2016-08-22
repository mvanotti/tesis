from statistics import mean, median, stdev, variance
import numpy as np
import matplotlib.mlab as mlab
import matplotlib.pyplot as plt

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
        bins = [x/4.0 for x in range(0, 41)]
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

def block_generation_graph(metrics):
    """ Generates a graph displaying how much time did each block (by number) took to appear on the network."""
    visited_blocks = set([])
    block_times_by_number = {}
    max_num = 0
    for m in metrics:
        if m["event"] != "broadcastBlock": continue
        num = m["number"]
        if num in visited_blocks: continue
        visited_blocks.add(num)

        block_times_by_number[num] = m
        if num > max_num: max_num = num

 #   max_num = 100
    block_times = [0] # Assume block #1 took 0ms ("starting block")
    for num in range(2, max_num + 1):
        delta = block_times_by_number[num]["timestamp"] - block_times_by_number[num - 1]["timestamp"]
        block_times.append(delta)

    plt.clf()
    plt.hist(block_times, bins=range(4900, 5500, 10), facecolor='g', alpha=0.75, cumulative=False)
    #plt.bar(range(1, 101), block_times)
    plt.show()
    plt.clf()
    return

def block_propagation_by_time(prop_times):
    #TODO(mvanotti): Complete this!
    return

def block_propagation(metrics):
    # Discard blocks from the beggining and end of the experiment.
    cutoff_time_end = metrics[-1]["timestamp"] - 60*1000*5
    cutoff_time_begin = metrics[0]["timestamp"] + 60*1000*5

    blocks = {}
    for m in [m for m in metrics if m["event"] in ["broadcastBlock", "newBlock"]]:
        hash = m["hash"]
        if hash not in blocks:
            blocks[hash] = []
        blocks[hash].append(m)

    propagation_times = {}
    for hash, ls in blocks.items():
        visited = set([])  # Only count the first time a node receives a block.
        start_time = ls[0]["timestamp"]
        if not (cutoff_time_begin < start_time < cutoff_time_end): continue
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