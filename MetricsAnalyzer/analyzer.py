from statistics import mean, median, stdev, variance
import numpy as np
import matplotlib.pyplot as plt
from os import path

from mpl_toolkits.axes_grid1 import host_subplot
import matplotlib.patches as mpatches
import mpl_toolkits.axisartist as AA


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
    percentages = {10:[], 50:[], 90:[], 95:[], 100:[]}
    indexes = [ min(int(x * nodes / 100.0), nodes) - 1 for x in sorted(percentages.keys())]
    for hash, times in prop_times.items():
        if len(times) < nodes:
            unreceived.append(hash)
            continue
        proptimes = [times[i][0] for i in indexes]
        percentages[10].append(proptimes[0])
        percentages[50].append(proptimes[1])
        percentages[90].append(proptimes[2])
        percentages[95].append(proptimes[3])
        percentages[100].append(proptimes[4])

    return percentages, unreceived


def propagation_histogram(prop_times, filePrefix, dstPath="/tmp/"):
    """
        Generates propagation histogram graphs.
        filePrefix is the prefix to use for the saved images.
        dstPath is the path in which images will be saved.
        generated files will be dstPath/filePrefix-cumulative.png
        generated files will be dstPath/filePrefix-noncumulative.png
    """
    noncumulative_filename = path.join(dstPath, "%s-noncumulative.png" % (filePrefix))
    cumulative_filename = path.join(dstPath, "%s-cumulative.png" % (filePrefix))
    data = []
    print("Calculating Histogram")
    for h, times in prop_times.items():
        data += [min(t[0], 10000.0) for t in times]
        # the histogram of the data

    cutoff_time = max(data)
    n, bins, patches = plt.hist(data, bins=range(0, cutoff_time, 50), facecolor='g', alpha=0.75, weights=100*(np.zeros_like(data) + 1. / len(data)), cumulative=True)
    plt.axis([0, cutoff_time, 0, 100])

    plt.xlabel('Seconds')
    plt.ylabel('cumulative %% of %s Received' % filePrefix)
    plt.title('Histogram of %s Propagation Times (cumulative)' % filePrefix)
    plt.grid(True)
    plt.savefig(filename=cumulative_filename)
    plt.clf()
    n, bins, patches = plt.hist(data, bins=range(0, cutoff_time, 50), facecolor='g', alpha=0.75, weights=100*(np.zeros_like(data) + 1. / len(data)), cumulative=False)
    plt.axis([0, cutoff_time, 0, 16])
    plt.xlabel('Seconds')
    plt.ylabel('%% of %s Received' % filePrefix)
    plt.title('Histogram of %s Propagation Times' % filePrefix)
    plt.grid(True)
    plt.savefig(filename=noncumulative_filename)
    plt.clf()

def groupBlocks(block_nums):
    dctCounter = {}
    prevBlock = 0
    prevBlockCounter = 0
    for n in block_nums:
        if prevBlock != n:
            dctCounter[prevBlock] = prevBlockCounter
            prevBlockCounter = 0
            prevBlock = n
        prevBlockCounter += 1
    return list(dctCounter.values())

def repeated_blocks_graph(blocks):
    block_nums = sorted([m["number"] for m in blocks])
    blocks_count = groupBlocks(block_nums)
    max_block_count = max(blocks_count)
    plt.clf()
    plt.hist(blocks_count, bins=range(1, max_block_count + 1, 1), facecolor='r', alpha=0.75, cumulative=False)
    plt.grid(True)
    #plt.show()
    #plt.show()


def plothist(deltas, s):
    plt.clf()
    #print(max(deltas))
    plt.hist(deltas, bins=range(0, int(max(deltas)), 2000), facecolor='b', alpha=0.75, cumulative=False)
    #plt.show()
    plt.clf()

def generation_graph(metrics, filePrefix, dstPath="/tmp/"):
    """
        Generates a graph displaying how much time did each block (by number) took to appear on the network.
        filePrefix is the prefix to use for the saved images.
        path is the path in which images will be saved.
    """
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


    block_times = [0] # Assume block #1 took 0ms ("starting block")
    block_diffs = [1, block_times_by_number[1]["difficulty"] / 10000.0]
    for num in range(2, max_num + 1):
        delta = block_times_by_number[num]["timestamp"] - block_times_by_number[num - 1]["timestamp"]
        block_times.append(delta)
        block_diffs.append(block_times_by_number[num]["difficulty"] / 10000.0)

    block_times = block_times[1:]
    plt.clf()
    plt.hist(block_times, bins = range(0, 70000, 1500), facecolor='b', alpha=0.75, cumulative=False)
    #plt.bar(range(1, 101), block_times)
    plt.xlabel("Generation time (milliseconds)")
    plt.ylabel("Amount of %s generated in that time" % filePrefix)
    plt.title("Histogram of %s generation times" % filePrefix)
    plt.grid(True)
    plt.savefig(filename=path.join(dstPath, "%s-generationhist.png" % filePrefix))
    plt.clf()

    y = np.array(block_times[1:])
    ydiffs = np.array(block_diffs[1:])
    xdiffs = np.array(range(1, len(ydiffs) + 1))
    x = np.array(range(1, len(y) + 1))

    ys = []
    tmp_sum = 0
    avg_size = 200
    for i in range(min(avg_size, len(y))):
        tmp_sum += y[i]
        ys.append(tmp_sum)
    for i in range(avg_size, len(y)):
        tmp_sum += y[i] - y[i - avg_size]
        ys.append(tmp_sum)

    for i in range(len(ys)):
        if i < avg_size:
            ys[i] /= float(i + 1)
        else:
            ys[i] /= float(avg_size)
    ys = np.array(ys)
    target = [30000 for x in ys]

    cyan = y < 10000
    azul = (y >= 10000) & (y < 20000)
    verde = (y >= 20000) & (y < 30000)
    amarillo = (y >= 30000) & (y < 40000)
    naranja = (y >= 40000) & (y < 50000)
    rojo = y > 50000

    fig = plt.figure(10, figsize=(80, 5), dpi=1000)
    plt.bar(x[cyan], y[cyan], color='#33adff', width=1.0)
    plt.bar(x[azul], y[azul], color='cyan', width=1.0)
    plt.bar(x[verde], y[verde], color='#1aff1a', width=1.0)
    plt.bar(x[amarillo], y[amarillo], color='yellow', width=1.0)
    plt.bar(x[naranja], y[naranja], color='orange', width=1.0)
    plt.bar(x[rojo], y[rojo], color='red', width=1.0)
    plt.plot(x, ys, '-', color='blue' )
    plt.plot(x, target, '-', color='red')

    plt.xlim(1, len(y))
    plt.xlabel("Block Number")
    plt.ylabel("Generation time (ms)")
    plt.savefig(filename=path.join(dstPath, "%s-generation.svg" % filePrefix), format="svg")
    plt.clf()

    fig.clear()
    plt.close()
    plt.clf()

    fig = plt.figure(111, figsize=(200, 5), dpi=500)
    host = host_subplot(111, axes_class=AA.Axes)
    plt.subplots_adjust(right=0.75)

    par1 = host.twinx()
    offset = 60

    host.bar(x[cyan], y[cyan], color='#33adff', width=1.0)
    host.bar(x[azul], y[azul], color='cyan', width=1.0)
    host.bar(x[verde], y[verde], color='#1aff1a', width=1.0)
    host.bar(x[amarillo], y[amarillo], color='yellow', width=1.0)
    host.bar(x[naranja], y[naranja], color='orange', width=1.0)
    host.bar(x[rojo], y[rojo], color='red', width=1.0)
    host.plot(x, ys, '-', color='blue')
    host.plot(x, target, '-', color='red')

    plt.xlim(1, len(y))
    host.set_ylim(0, max(y))
    plt.xlabel("Block Number")
    host.set_ylabel("Generation time (ms)")
    par1.set_ylabel("Difficulty / 10000")
    par1.get_xaxis().get_major_formatter().set_scientific(False)
    par1.get_xaxis().get_major_formatter().set_useOffset(False)
    print(ydiffs[-10:])

    par1.plot(xdiffs, ydiffs, '-', color="green", linewidth=2.0)

    green_patch = mpatches.Patch(color='green', label='Block Difficulty')
    blue_patch = mpatches.Patch(color='blue', label='Rolling Average of Generation Times')
    red_patch = mpatches.Patch(color='red', label='Target Duration')
    plt.legend(handles=[red_patch, blue_patch, green_patch])

    plt.savefig(filename=path.join(dstPath, "%s-generation-diff.png" % filePrefix), format="png")
    return

def block_propagation_by_time(prop_times):
    #TODO(mvanotti): Complete this!
    return

def block_propagation(metrics):
    # Discard blocks from the beggining and end of the experiment.
    #cutoff_time_end = metrics[-1]["timestamp"] - 60*1000*5

    cutoff_time_end = metrics[0]["timestamp"] + 60*1000*60*11
    cutoff_time_begin = metrics[0]["timestamp"] + 60*1000*5

    blocks = {}
    for m in metrics:
        if m["event"] not in ["broadcastBlock", "newBlock"]: continue

        hash = m["hash"]
        if hash not in blocks:
            blocks[hash] = []
        blocks[hash].append(m)

    propagation_times = {}
    for hash, ls in blocks.items():
        numbers = set()
        visited = set([])  # Only count the first time a node receives a block.
        start_time = ls[0]["timestamp"]
        if not (cutoff_time_begin < start_time < cutoff_time_end): continue
        if ls[0]["event"] != "broadcastBlock":
            print("Block with hash %s received appeared out of order!" % ls[0]["hash"])
            continue

        # times is a list of (elapsedTime, node).
        # for each node, how long did it take to receive the block.
        times = [(0, ls[0]["nodeID"])]
        visited.add(ls[0]["nodeID"])
        ls = [m for m in ls if m["event"] == "newBlock"]
        for m in ls:
            node = m["nodeID"]
            if node in visited: continue
            visited.add(node)
            numbers.add(m["number"])
            if len(numbers) > 1: print("Repeated block with hash %s" % hash)

            elapsed = m["timestamp"] - start_time
            if elapsed > 5000: print(m["hash"], elapsed)
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