import unittest
from parser import parseMetric



class ParserTest(unittest.TestCase):
    def test(self):
        tests = [
            {
                "input": "",
                "output": None,
            },
            {
                "input": "18:06:46.711 INFO [metrics]  950a92 at: 1468271206709 nano: 37149209913793 | event: broadcastBlock hash: 7da33b number: 1 parent: a7f584 ",
                "output": {
                    'nodeID': "950a92",
                    'timestamp': int(1468271206709),
                    'nano': int(37149209913793),
                    'event': "broadcastBlock",
                    'hash': "7da33b",
                    'number': int(1),
                    'parent': "a7f584",
                    'difficulty': 1,
                }
            },
            {
                "input": "15:01:35.647 INFO [metrics]  950a92 at: 1473271295647 nano: 18065921990182 | event: broadcastBlock hash: 77fe09 number: 49 parent: b2633e diff: 3150315 ",
                "output": {
                    'nodeID': "950a92",
                    'timestamp': int(1473271295647),
                    'nano': int(18065921990182),
                    'event': "broadcastBlock",
                    'hash': "77fe09",
                    'number': int(49),
                    'parent': "b2633e",
                    'difficulty': 3150315,
                }
            },
            {
                "input": "18:06:53.877 INFO [metrics]  950a92 at: 1468271213877 nano: 37156378218820 | event: messageBytes bytes: 74 sender: 2bc32a ",
                "output": {
                    'nodeID': "950a92",
                    'timestamp': int(1468271213877),
                    'nano': int(37156378218820),
                    'event': "messageBytes",
                    'bytes': "74",
                    'sender': "2bc32a",
                }
            },
            {
                "input": "18:06:53.903 INFO [metrics]  2bc32a at: 1468271213903 nano: 37156404110824 | event: newBlock hash: 3d35d0 number: 2 parent: 7da33b sender: 950a92 ",
                "output": {
                    'nodeID': "2bc32a",
                    'timestamp': int(1468271213903),
                    'nano': int(37156404110824),
                    'event': "newBlock",
                    'hash': "3d35d0",
                    'number': int(2),
                    'parent': "7da33b",
                    'sender': "950a92"
                }
            },
            {
                "input": "18:34:50.413 INFO [metrics]  2bc32a at: 1468272890413 nano: 38832914110443 | event: broadcastTransaction hash: 914018 nonce: 3 ",
                "output": {
                    'nodeID': "2bc32a",
                    'timestamp': int(1468272890413),
                    'nano': int(38832914110443),
                    'event': "broadcastTransaction",
                    'hash': "914018",
                    'nonce': int(3),
                }
            },
            {
                "input": "18:46:07.633 INFO [metrics]  950a92 at: 1468273567633 nano: 39510134143559 | event: newTransaction hash: 1d5fd8 nonce: 3 sender: 2bc32a ",
                "output": {
                    'nodeID': "950a92",
                    'timestamp': int(1468273567633),
                    'nano': int(39510134143559),
                    'event': "newTransaction",
                    'hash': "1d5fd8",
                    'nonce': int(3),
                    'sender': "2bc32a"
                }
            },
            {
                "input": "17:27:29.805 INFO [metrics]  27ff51 at: 1468355249805 nano: 24196264880663 | event: newBlockHash hash: dcbd6a number: 148 sender: 950a92 ",
                "output": {
                    'nodeID': "27ff51",
                    'timestamp': int(1468355249805),
                    'nano': int(24196264880663),
                    'event': "newBlockHash",
                    'hash': "dcbd6a",
                    'number': int(148),
                    'sender': "950a92"
                }
            },
            {
                "input": "18:46:07.633 INFO this should not be considered.",
                "output": None,
            }
        ]
        for test in tests:
            self.assertEqual(parseMetric(test["input"]), test["output"])


if __name__ == "__main__":
    unittest.main()
