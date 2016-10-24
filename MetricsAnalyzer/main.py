from sys import stdin
from parser import parseMetric, parseSimgridMetric
from analyzer import calculateTimeDifferencesAllHosts
from analyzer import block_propagation, transaction_propagation
from analyzer import propagation_histogram, generation_graph, propagation_statistics, repeated_blocks_graph
from analyzer import plothist
from statistics import mean, median, stdev, variance
from blockchain import Block, Blockchain
import random


def group_blocks_by_sender(blocks):
    """ returns a dictionary whose keys are the miner's nodeIds, and the values are lists of all blocks mined by that miner. """
    res = {}

    # Group blocks by miner.
    for b in blocks:
        if b["nodeID"] not in res:
            res[b["nodeID"]] = []
        res[b["nodeID"]].append(b)

    # Calculate generation statistics.
    for s in res.keys():
        print("Miner: %s | blocks: %d" % (s, len(res[s])))
        ts1 = sorted([m["timestamp"] for m in res[s]])
        ts2 = [0] + ts1
        deltas = [(ts1[i] - ts2[i]) for i in range(len(ts1))][1:]
        #print("Mean: %.4f Median: %.4f Std: %.4f, blocks: %d" % (mean(deltas), median(deltas), stdev(deltas), len(deltas)))
        #plothist(deltas, s)

    print("Global Info")
    ts1 = sorted([m["timestamp"] for m in blocks])
    ts2 = [0] + ts1
    deltas = [(ts1[i] - ts2[i]) for i in range(len(ts1))][1:]
    print("Mean: %.4f Median: %.4f Std: %.4f, blocks: %d" % (mean(deltas), median(deltas), stdev(deltas), len(deltas)))
    print("Min: %d Max: %d" % (min(deltas), max(deltas)))
    plothist(deltas, "Global Info")
    return res

def take_first(metrics, cutoff):
    cutoff_time = metrics[0]["timestamp"] + cutoff
    return [m for m in metrics if m["timestamp"] <= cutoff_time]

def discard_last(metrics, cutoff):
    cutoff_time = metrics[-1]["timestamp"] - cutoff
    return [m for m in metrics if m["timestamp"] <= cutoff_time]

def take_first_blocks(metrics, cutoff):
    return [m for m in metrics if "number" not in m or m["number"] <= cutoff]

def find_genesis(metrics):
    for m in metrics:
        if "number" in m and m["number"] == 1: return m["parent"]
    return None

def main():
    """ Usage: python parser.py < logfile """
    metrics = []
    nodes = set([])
    for line in stdin:
        metric = parseSimgridMetric(line)
        if metric is None: continue
        metrics.append(metric)
        nodes.add(metric["nodeID"])

    metrics = linearize(metrics)
    #  calculateTimeDifferencesAllHosts(metrics)
    # We need at least 10 minutes of data.
    if metrics[-1]["timestamp"] - metrics[0]["timestamp"] < 1000 * 60 * 10:
        print("Not enough data! %.2f minutes" % ((metrics[-1]["timestamp"] - metrics[0]["timestamp"]) / (60.0 * 1000.0)))
        return

    #metrics = take_first(metrics, 11 * 60 * 60 * 1000) # Keep only the first 11 hours of metrics.
    metrics = take_first_blocks(metrics, 1001)         # Keep only the first 1k blocks.

    all_blocks = get_all_blocks_hashes(metrics)
    print("Total unique blocks sent: %d" % len(all_blocks))

    blocks_by_sender = group_blocks_by_sender(get_all_broadcasted_blocks_by_number(metrics))
    genesis = Block({"hash": find_genesis(metrics), "parent": "000000", "timestamp":0, "number":0, "nodeID": "000000", "difficulty": 1})
    blockchain = Blockchain(genesis)

    generation_graph(metrics, "blocks")

    blocks = get_all_broadcasted_blocks(metrics)
    for metric in blocks:
        block = Block(metric)
        blockchain.add_block(block)

    print("Calculating forks depth")
    print(blockchain.count_forks_depth())
    print("Calculating amount of competing blocks")
    print(blockchain.count_repeated_blocks())

    block_prop_times = block_propagation(metrics)
    block_stats, unreceived = propagation_statistics(len(nodes), block_prop_times)
    print("Blocks not received by everyone: %d/%d" % (len(unreceived), len(block_prop_times)))
    for k in random.sample(unreceived, min(30, len(unreceived))):
        print(k, len(block_prop_times[k]))

    propagation_histogram(block_prop_times, "blocks")


    for p in sorted(block_stats.keys()):
        vals = block_stats[p]
        print("Blocks propagated to %d%% of nodes in:" % p)
        if (len(vals)) < 10:
            print("Not enough data!")
            return
        print("mean: %d, median: %d, max: %d, min: %d, stddev: %d, variance: %d" %
              (mean(vals), median(vals), max(vals), min(vals), stdev(vals), variance(vals)))

    tx_prop_times = transaction_propagation(metrics)
    tx_stats, unreceived = propagation_statistics(len(nodes), tx_prop_times)
    print("Txs not received by everyone: %d/%d" % (len(unreceived), len(tx_prop_times)))

    for p in sorted(tx_stats.keys()):
        vals = tx_stats[p]
        print("Txs propagated to %d%% of nodes in:" % p)
        if (len(vals) < 10):
            print("Not enough data!")
            break
        print("mean: %d, median: %d, max: %d, min: %d, stddev: %d, variance: %d" %
              (mean(vals), median(vals), max(vals), min(vals), stdev(vals), variance(vals)))

    #propagation_histogram(tx_prop_times, "txs")

    blocks = get_all_broadcasted_blocks(metrics)
    repeated_blocks_graph(blocks)
    #print(get_blocks_by_number(blocks))

def linearize(metrics):
    return sorted(metrics, key=lambda m: int(m["timestamp"]))

def get_all_blocks_hashes(metrics):
    """ Returns all different block hashes """
    return set([m["hash"] for m in metrics if m["event"] in ["broadcastBlock", "newBlock", "newBlockHash"]])

def get_all_broadcasted_blocks(metrics):
    """Returns, a list that contains for each broadcasted block, the first appearence. """
    visited = set([])
    res = []
    for m in metrics:
        if m["event"] != "broadcastBlock": continue
        if (m["hash"], m["number"]) in visited: continue
        visited.add((m["hash"], m["number"]))
        res.append(m)
    return res

def get_all_broadcasted_blocks_by_number(metrics):
    """Returns, a list that contains for each broadcasted block (number), the first appearence. """
    visited = set([])
    res = []
    for m in metrics:
        if m["event"] != "broadcastBlock": continue
        if m["number"] in visited: continue
        visited.add(m["number"])
        res.append(m)
    return res

def get_blocks_by_number(blocks):
    bbn = {}
    for m in blocks:
        n = m["number"]
        if n not in bbn:
            bbn[n] = 0
        bbn[n] += 1
    return bbn

if __name__ == "__main__":
    main()