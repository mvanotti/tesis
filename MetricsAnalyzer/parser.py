from sys import stdin
import json

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
        visited = set([]) # Only count the first time a node receives a block.
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
        visited = set([]) # Only count the first time a node receives a block.
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

def main():
    metrics = []
    nodes = set([])
    for line in stdin:
        metric = parseMetric(line)
        if metric == None: continue
        metrics.append(metric)

    metrics = linearize(metrics)
    print "var nodes = ", json.dumps(list(nodes)), ";"
    print "var data = ", json.dumps(metrics), ";"
    propTimes = blockPropagation(metrics)
    #for hash, times in propTimes.iteritems():
        #print "Block %s propagated in %d" % (hash, times[-1][0])

    txTimes = txPropagation(metrics)
    #for hash, times in txTimes.iteritems():
        #print "Tx %s propagated in %d" % (hash, times[-1][0])

    bwInfo = getBandwithUsage(metrics)




if __name__ == "__main__":
    main()