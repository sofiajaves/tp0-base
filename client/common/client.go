package common

import (
	"bufio"
	"fmt"
	"net"
	"time"
	"os"
	"os/signal"
	"syscall"

	"github.com/op/go-logging"
)

var log = logging.MustGetLogger("log")

// ClientConfig Configuration used by the client
type ClientConfig struct {
	ID            string
	ServerAddress string
	LoopAmount    int
	LoopPeriod    time.Duration
}

// Client Entity that encapsulates how
type Client struct {
	config ClientConfig
	conn   net.Conn
	isFinished bool
}

// NewClient Initializes a new client receiving the configuration
// as a parameter
func NewClient(config ClientConfig) *Client {
	client := &Client{
		config: config,
		isFinished: false,
	}
	InitializeSignalListener(client)
	return client
}

func InitializeSignalListener(client *Client) {
	sigs := make(chan os.Signal, 1)

	signal.Notify(sigs, syscall.SIGTERM)
	go func(client *Client) {
		sig := <-sigs
		log.Infof("action: received termination signal | result: in_progress | signal: %s", sig)
		err := client.Shutdown()
	
	if err != nil {
		log.Infof("action: received termination signal | result: error | signal: %s | error: %v", sig, err)
		return
	}
	log.Infof("action: received termination signal | result: success | signal: %s", sig)
	}(client)
}

// CreateClientSocket Initializes client socket. In case of
// failure, error is printed in stdout/stderr and exit 1
// is returned
func (c *Client) createClientSocket() error {
	conn, err := net.Dial("tcp", c.config.ServerAddress)
	if err != nil {
		log.Criticalf(
			"action: connect | result: fail | client_id: %v | error: %v",
			c.config.ID,
			err,
		)
		return err
	}
	c.conn = conn
	return nil
}

func (c *Client) Shutdown() error {
	c.conn.Close()
	c.isFinished = true
	return nil
}

// StartClientLoop Send messages to the client until some time threshold is met
func (c *Client) StartClientLoop() {
	// autoincremental msgID to identify every message sent
	msgID := 1

	loop:
		// Send messages if the loopLapse threshold has not been surpassed
		for timeout := time.After(c.config.LoopPeriod * time.Duration(c.config.LoopAmount)); !c.isFinished; {
			select {
			case <-timeout:
				log.Infof("action: timeout_detected | result: success | client_id: %v",
					c.config.ID,
				)
				break loop
			default:
			}
			// Create the connection the server in every loop iteration. Send an
			c.createClientSocket()
			// TODO: Modify the send to avoid short-write
			fmt.Fprintf(
				c.conn,
				"[CLIENT %v] Message N°%v\n",
				c.config.ID,
				msgID,
			)
			msg, err := bufio.NewReader(c.conn).ReadString('\n')
			msgID++
			c.conn.Close()

			if err != nil {
				log.Errorf("action: receive_message | result: fail | client_id: %v | error: %v",
					c.config.ID,
					err,
				)
				return
			}
			log.Infof("action: receive_message | result: success | client_id: %v | msg: %v",
				c.config.ID,
				msg,
			)

			// Wait a time between sending one message and the next one

			if !c.isFinished {
				time.Sleep(c.config.LoopPeriod)
			}
		}

		log.Infof("action: loop_finished | result: success | client_id: %v", c.config.ID)
}