//p2p Test is a program that tests TCP connections in a p2p network (assuming all hosts run in the same net, with continuous addresses starting from 10.0.0.1)
//the way this program testes the network is by creating a connection between each pair of nodes (each node connects to the nodes with IPs lower than them) and sending messages.
package main

import (
	"bufio"
	"encoding/gob"
	"flag"
	"fmt"
	"io"
	"log"
	"net"
	"os"
	"sync"
	"time"
)

var (
	h         = flag.Int("h", 0, "Host ID (must be unique)")
	peersFile = flag.String("f", "peers", "File containing peer addresses and ports, in 'addr:port' format")
	numPings  = flag.Int("np", 30, "Number of ping requests to send")
)

const (
	REQUEST uint8 = 1
	REPLY   uint8 = 2
)

type work struct {
	Sender   int32
	Type     uint8
	Number   int32
	UnixNano int64
}

type Encoder interface {
	Encode(data interface{}) error
}

type Decoder interface {
	Decode(data interface{}) error
}

type gobWrapper struct {
	Encoder
	Decoder
	io.Closer
}

func newGobWrapper(conn net.Conn) gobWrapper {
	return gobWrapper{Encoder: gob.NewEncoder(conn), Decoder: gob.NewDecoder(conn), Closer: conn}
}

func sendPings(enc Encoder) {
	for i := 0; i < *numPings; i++ {
		q := work{Sender: int32(*h), Number: int32(i), UnixNano: time.Now().UnixNano()}
		sendData(enc, q)
		time.Sleep(1 * time.Second)
	}
}

func handleConn(conn net.Conn) {
	gob := newGobWrapper(conn)
	defer gob.Close()
	go sendPings(gob)

	deltasList := []int64{}
	deltasSum := int64(0)
	for {
		var q work
		err := gob.Decode(&q)
		if err != nil {
			log.Fatal(err)
		}
		if q.Type == REPLY {
			delta := time.Now().UnixNano() - q.UnixNano
			deltasSum += delta
			deltasList = append(deltasList, delta)
			deltaSeconds := float64(delta) / float64(time.Second)
			avgSeconds := float64(deltasSum) / (float64(time.Second) * float64(len(deltasList)))
			log.Printf("reply from: %d. Number: %d, it took: %.4f seconds, avg: %.4f seconds", q.Sender, q.Number, deltaSeconds, avgSeconds)
		} else {
			//log.Printf("received message from: %d. Number: %d", q.Sender, q.Number)
			w := work{Sender: int32(*h), Number: q.Number, Type: REPLY, UnixNano: q.UnixNano}
			sendData(gob, w)
		}
	}
}

func sendData(enc Encoder, q work) {
	if err := enc.Encode(q); err != nil {
		log.Fatal(err)
	}
}

func serverListener(lstAddr string, wg *sync.WaitGroup) {
	ln, err := net.Listen("tcp", lstAddr)
	if err != nil {
		log.Fatal(err)
	}
	defer ln.Close()

	log.Println("Listening for connections!", ln.Addr())
	conncha := make(chan net.Conn, 10)
	go func() {
		for {
			conn, err := ln.Accept()
			if err != nil {
				log.Fatal(err)
			}
			log.Println("Handling new connection!", conn.RemoteAddr())
			conncha <- conn
		}
	}()

	for {
		select {
		case conn := <-conncha:
			go handleConn(conn)
		case <-time.After(time.Minute + time.Duration(*numPings)*3*time.Second):
			wg.Done()
			return
		}
	}
}

func parsePeers(path string) []string {
	f, err := os.Open(path)
	if err != nil {
		log.Fatal(err)
	}
	defer f.Close()

	ls := []string{}
	scanner := bufio.NewScanner(f)
	for scanner.Scan() {
		ls = append(ls, scanner.Text())
	}
	if err := scanner.Err(); err != nil {
		log.Fatal(err)
	}

	return ls
}

func main() {
	flag.Parse()
	peers := parsePeers(*peersFile)
	log.SetPrefix(fmt.Sprintf("[%d] ", *h))

	var wg sync.WaitGroup
	wg.Add(1)
	go serverListener(peers[*h], &wg)

	for i := 0; i < *h; i++ {
		wg.Add(1)
		go func(i int) {
			defer wg.Done()
			conn := tryConnect(peers[i])
			go handleConn(conn)
		}(i)
	}
	wg.Wait()
}

func tryConnect(dst string) net.Conn {
	for i := 0; i < 10; i++ {
		var err error
		conn, err := net.Dial("tcp", dst)
		if err != nil {
			retryTime := 5 * (1 << uint(i))
			log.Printf("Failed to connect to %q. Retrying in %d seconds. err: %+v", dst, retryTime, err)
			time.Sleep(time.Second * time.Duration(retryTime))
			continue
		}
		return conn
	}
	log.Fatal("Could not connect")
	return nil
}
