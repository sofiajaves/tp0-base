package common

import (
	"fmt"
	"os"
	"io"
)

type BetAgency struct {
	client *Client
}

func NewBetAgency(client_config ClientConfig) *BetAgency {
		client := NewClient(client_config)

		bet_agency := &BetAgency{
			client: client,
		}

	return bet_agency
}

func (agency *BetAgency) Start() {
	file, err := os.Open(fmt.Sprintf("/dataset/agency-%s.csv", agency.client.config.ID))
	if err != nil {
		log.Errorf("action: start bet agency | result: fail | client_id: %v | error: %v", agency.client.config.ID, err)
		return
	}

	defer file.Close()
	
	
	err = agency.client.createClientSocket()
	
	if err != nil {
		return
	}
	defer agency.client.Shutdown()

	for {
		bets, err := readBets(file, agency.client.config.ID, agency.client.config.MaxAmount)
		if err != nil {
			if err == io.EOF {
				log.Infof("action: read_bets | result: success | client_id: %v | message: EOF", agency.client.config.ID)
				break
			} else {
				log.Errorf("action: read_bets | result: fail | client_id: %v | error: %v", agency.client.config.ID, err)
			}
			return
		}
		agency.SendBets(bets)
	}
}

func (agency *BetAgency) SendBets(bets []*Bet) {
	serializedBets := serializeMultipleBets(bets)
	agency.client.SendMsg(serializedBets)
}