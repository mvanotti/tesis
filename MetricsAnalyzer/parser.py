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
        "difficulty": int(metric[9]) if len(metric) > 9 else 1
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

def parseSimgridMetric(line):
    # Example (simgrid): [3_US:MessageHandler:(5) 35778.732184] [jmsg/INFO] at: 35778732 nano: 0 | event: newBlock hash: d3e298 number: 3344 parent: 6dd796 sender: 1_CN
    metric = line.strip().split(' ')
    if len(metric) < 12: return None
    nodeID = metric[0].split(':')[0][1:]
    timestamp = metric[4]
    nano = 0
    event = metric[9]

    if event not in metricsParser: return None

    metric = metricsParser[event](metric[8:])
    metric["nodeID"] = nodeID
    metric["timestamp"] = int(timestamp)
    metric["nano"] = int(nano)
    return metric

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
