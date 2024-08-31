package common

import (
	"fmt"
	"os"

	"github.com/op/go-logging"
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

func (bet_agency *BetAgency) SendBet() {
	bet := bet_agency.bet
	err := bet_agency.client.StartClient(bet.serialize())

	if err != nil {
		log.Errorf("action: send_bet | result: fail | client_id: %v | error: %v", 
			bet_agency.client.config.ID, err)
		return
	}

	log.Infof("action: send_bet | result: success | client_id: %v", bet_agency.client.config.ID)
}

func (agency *BetAgency) Start() {
	file, err := osOpen(fmt.Sprintf("/dataset/agency-%s.csv"), agency.client.config.ID)
	
	defer file.Close()
	defer agency.client.Shutdown()

	if err != nil {
		log.Errorf("action: start bet agency | result: fail | client_id: %v | error: %v", agency.client.config.ID, err)
		return
	}

	err = agency.client.CreateClientSocket()

	if err != nil {
		return
	}

	for {
		bets, err := readBets(file, agency.client.config.ID, agency.client.config.MaxAmount)
		if err != nil {
			log.Errorf("action: read_bets | result: fail | client_id: %v | error: %v", agency.client.config.ID, err)
			return
		}
		agency.SendBets(bets)
	}
}

func (agency *BetAgency) SendBets(bets []*Bet) {
	serializedBets := serializeMultipleBets(bets)
	agency.client.SendMsg(serializedBets)
}