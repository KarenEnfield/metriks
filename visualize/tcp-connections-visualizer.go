package main

import (
	"encoding/json"
	"fmt"
	"log"
	"os"
	"os/signal"
	"sync"
	"syscall"

	"github.com/Shopify/sarama"
	"github.com/gonum/graph"
	"github.com/gonum/graph/simple"
)

var (
	exitFlag  = false
	graphLock sync.Mutex
)

func sigintHandler() {
	exitFlag = true
	fmt.Println("\nSIGINT received!")
}

func main() {
	signalChan := make(chan os.Signal, 1)
	signal.Notify(signalChan, syscall.SIGINT)

	go func() {
		for {
			sig := <-signalChan
			switch sig {
			case syscall.SIGINT:
				sigintHandler()
				return
			}
		}
	}()

	kafkaBootstrapServers := "kafka-container:9092"
	tcpConnectionsTopic := "tcp-events"
	consumerGroup := "your-consumer-group" // Replace with your actual consumer group

	config := sarama.NewConfig()
	config.Consumer.Offsets.Initial = sarama.OffsetOldest

	consumer, err := sarama.NewConsumer([]string{kafkaBootstrapServers}, config)
	if err != nil {
		log.Fatalf("Failed to create Kafka consumer: %v", err)
	}
	defer func() {
		if err := consumer.Close(); err != nil {
			log.Printf("Error closing Kafka consumer: %v", err)
		}
	}()

	topic := []string{tcpConnectionsTopic}
	partitionConsumer, err := consumer.ConsumePartition(topic[0], 0, sarama.OffsetNewest)
	if err != nil {
		log.Fatalf("Failed to create partition consumer: %v", err)
	}
	defer func() {
		if err := partitionConsumer.Close(); err != nil {
			log.Printf("Error closing partition consumer: %v", err)
		}
	}()

	graph := simple.NewDirectedGraph()

	graphMax := 25
	edgeCount := 0

	for !exitFlag {
		select {
		case msg := <-partitionConsumer.Messages():
			if msg == nil {
				continue
			}

			var data map[string]interface{}
			if err := json.Unmarshal(msg.Value, &data); err != nil {
				log.Printf("Error decoding JSON: %v ; Skip %s", err, msg.Value)
				continue
			}

			srcIP := data["src_ip"].(string)
			destIP := data["dest_ip"].(string)
			srcPort := int(data["src_port"].(float64))
			destPort := int(data["dest_port"].(float64))

			srcID := fmt.Sprintf("%s_%d", srcIP, srcPort)
			destID := fmt.Sprintf("%s_%d", destIP, destPort)

			if srcPort+destPort == 0 || srcIP == destIP {
				continue // Skip
			}

			graphLock.Lock()
			// Check if the edge already exists
			if !edgeExists(graph, srcID, destID) {
				// Create a new edge
				graph.SetEdge(graph.NewEdge(graph.Node(srcID), graph.Node(destID)))
				edgeCount++
			}
			graphLock.Unlock()

			fmt.Printf("Src IP: %s, Dest IP: %s, Src Port: %d, Dest Port: %d\n", srcIP, destIP, srcPort, destPort)
		}
	}

	// Visualize the graph (using external libraries)

	fmt.Printf("Metriks TCP: %d connections (IP+port)\n", edgeCount)
	fmt.Printf("Number of nodes: %d\n", graph.NodeCount())
	fmt.Printf("Number of edges: %d\n", graph.EdgeCount())
}

func edgeExists(g graph.Graph, src, dest string) bool {
	nodes := g.Nodes()
	for nodes.Next() {
		if nodes.Node().ID().(string) == src {
			neighbors := g.From(nodes.Node().ID())
			for neighbors.Next() {
				if neighbors.Node().ID().(string) == dest {
					return true
				}
			}
			return false
		}
	}
	return false
}
