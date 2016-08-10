// configGen generates the rootstock config given a set of nodeIds.json files.
package main

import (
	"encoding/json"
	"flag"
	"fmt"
	"io/ioutil"
	"log"
	"math/rand"
	"os"
	"path/filepath"
	"strings"
	"text/template"
	"time"
)

type nodeID struct {
	PrivateKey string
	PublicKey  string
	Address    string
	NodeID     string
}

var (
	maxNodes     = flag.Int("n", 20, "Maximum Amount of Nodes")
	nodesFolder  = flag.String("ndir", "nodeids", "Folder in which to find all the json files with the nodes description")
	cantMiners   = flag.Int("m", 5, "Miners amount")
	minPeers     = flag.Int("minP", 3, "Minimum amount of peers")
	maxPeers     = flag.Int("maxP", 9, "Maximum amount of peers")
	configFolder = flag.String("cdir", "configs", "Folder in which to store all the generated configuration files")
)

type node struct {
	Ip          string
	Port        string
	Minerclient bool
	Minerserver bool
	Id          nodeID
	Peers       []int
}

func main() {
	flag.Parse()
	rand.Seed(time.Now().UnixNano())

	nodeIDs := parseNodeIDs(*nodesFolder, *maxNodes)
	nodeIPs := genNodeIPs(*maxNodes)

	nodes := getNodes(nodeIDs, nodeIPs)

	addMiners(nodes, *cantMiners)
	addPeers(nodes, *minPeers, *maxPeers)

	keepOneWayPeers(nodes)

	saveConfigs(nodes, *configFolder)
	saveConnectivityGraph(nodes, filepath.Join(*configFolder, "connectivity.dot"))
}

func keepOneWayPeers(nodes []node) {
	for i, _ := range nodes {
		peers := nodes[i].Peers
		nodes[i].Peers = []int{}
		for _, v := range peers {
			if v < i {
				nodes[i].Peers = append(nodes[i].Peers, v)
			}
		}
	}
}

func saveConnectivityGraph(nodes []node, path string) {
	w, err := os.Create(path)
	if err != nil {
		log.Fatalf("failed to create config file: %+v", err)
	}
	tmpltData, err := ioutil.ReadFile("conntemplate")
	if err != nil {
		log.Fatal(err)
	}
	var tmplt = template.Must(template.New("conn").Parse(string(tmpltData)))
	d := struct {
		Nodes []node
	}{nodes}
	if err := tmplt.Execute(w, d); err != nil {
		log.Fatal(err)
	}
}

func saveConfigs(nodes []node, path string) {
	tmpltData, err := ioutil.ReadFile("template")
	if err != nil {
		log.Fatal(err)
	}
	var tmplt = template.Must(template.New("rslt").Parse(string(tmpltData)))

	for i := 0; i < len(nodes); i++ {
		saveConfig(i, nodes, filepath.Join(path, fmt.Sprintf("node%s.conf", nodes[i].Ip)), tmplt)
	}
}

func saveConfig(n int, nodes []node, path string, tmplt *template.Template) {
	w, err := os.Create(path)
	if err != nil {
		log.Fatalf("failed to create config file: %+v", err)
	}

	d := struct {
		Name  string
		N     node
		Nodes []node
	}{N: nodes[n], Nodes: nodes, Name: fmt.Sprintf("node%d", n+1)}
	if err := tmplt.Execute(w, d); err != nil {
		log.Fatal(err)
	}
}

// addMiners sets "miners" of the given nodes as miners.
func addMiners(nodes []node, miners int) {
	for i := 0; i < miners; i++ {
		k := rand.Intn(len(nodes))
		for nodes[k].Minerclient {
			k = rand.Intn(len(nodes))
		}

		nodes[k].Minerclient = true
		nodes[k].Minerserver = true
	}
}

// addPeers adds a random number of peers (between minPeers and maxPeers) to each node.
func addPeers(nodes []node, minPeers int, maxPeers int) {
	for i := 1; i < len(nodes); i++ {
		log.Printf("node %d: connected to graph.", i)
		addToGraph(i, nodes, maxPeers)
	}
	// So far we have a connected graph, try to connect each node randomly to up to minPeers without violating maxPeers.
	for i := 1; i < len(nodes); i++ {
		log.Printf("node %d: adding peers.", i)
		addPeersToNode(i, nodes, minPeers, maxPeers)
	}
}

// addToGraph connects a node with one of the nodes below it.
func addToGraph(n int, nodes []node, maxPeers int) {
	added := false
	for !added {
		k := rand.Intn(n)
		if len(nodes[k].Peers) >= maxPeers {
			continue
		}
		nodes[n].Peers = append(nodes[n].Peers, k)
		nodes[k].Peers = append(nodes[k].Peers, n)
		added = true
	}
}

// addPeersToNode adds peers to the given node until it reaches minPeers.
func addPeersToNode(n int, nodes []node, minPeers, maxPeers int) {
	for len(nodes[n].Peers) < minPeers {
		k := rand.Intn(len(nodes))
		if k == n {
			continue
		}
		if len(nodes[k].Peers) == maxPeers {
			continue
		}
		if areConnected(nodes, n, k) {
			continue
		}
		log.Printf("node %d: adding peer %d", n, k)
		nodes[n].Peers = append(nodes[n].Peers, k)
		nodes[k].Peers = append(nodes[k].Peers, n)
		break
	}
}

func areConnected(nodes []node, n, k int) bool {
	for i := 0; i < len(nodes[n].Peers); i++ {
		if nodes[n].Peers[i] == k {
			return true
		}
	}
	return false
}

// getNodes generates a list of node{} with the given nodeIDs and nodeIPs
func getNodes(nodeIDs []nodeID, nodeIPs []string) []node {
	res := []node{}
	for i := range nodeIDs {
		id := nodeIDs[i]
		ip := nodeIPs[i]

		res = append(res, node{Ip: ip, Port: "30305", Minerclient: false, Minerserver: false, Id: id})
	}

	return res
}

// parseNodeIDs parses all the files in the given folder that end in .json, and returns up to maxNodes nodeIDs.
func parseNodeIDs(path string, maxNodes int) []nodeID {
	log.Printf("Parsing up to %d nodes from folder %q", maxNodes, path)
	files, err := ioutil.ReadDir(path)
	if err != nil {
		log.Fatalf("failed to read dir: %q. err: %+v", path, err)
	}

	filesToParse := []string{}

	for _, f := range files {
		if strings.HasSuffix(f.Name(), ".json") {
			filesToParse = append(filesToParse, f.Name())
		}
	}
	filesToParse = filesToParse[:maxNodes]

	res := []nodeID{}
	for _, f := range filesToParse {
		nid := parseNodeID(filepath.Join(path, f))
		res = append(res, nid)
	}

	return res
}

// parseNodeID parses a json-encoded file with a nodeId information.
func parseNodeID(path string) nodeID {
	data, err := ioutil.ReadFile(path)
	if err != nil {
		log.Fatalf("failed to read file: %q. err: %+v", path, err)
	}
	var nid nodeID
	if err := json.Unmarshal(data, &nid); err != nil {
		log.Fatalf("failed to parse nodeid: %q. err: %+v", path, err)
	}

	return nid
}

// genNodeIPs generates ips for the desired amount of nodes. Starting from 10.0.0.1 and up to 10.0.0.254
func genNodeIPs(maxNodes int) []string {
	if maxNodes >= 255 {
		log.Fatal("can't create more than 254 nodes")
	}
	ips := []string{}
	for i := 1; i <= maxNodes; i++ {
		ip := fmt.Sprintf("10.0.0.%d", i)
		ips = append(ips, ip)
	}
	return ips
}
