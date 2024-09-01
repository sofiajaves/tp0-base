package common

import (
	"fmt"
	"os"
	"io"
	"strings"
	"time"
)

const WAITING_MESSAGE = "waiting"
const WINNER_SEPARATOR = ","
const CSV_SEPARATOR = ";"

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

func (agency *BetAgency) StartBetSendingProcess() error {
	file, err := os.Open(fmt.Sprintf("/dataset/agency-%s.csv", agency.client.config.ID))
	if err != nil {
		log.Errorf("action: open_file | result: fail | client_id: %v | error: %v", agency.client.config.ID, err)
		return err
	}

	defer file.Close()
	
	
	err = agency.client.createClientSocket()
	
	if err != nil {
		return err
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
			return err
		}
		agency.SendBets(bets)
	}
	return nil
}

func (agency *BetAgency) Start() {
	if err := agency.StartBetSendingProcess(); err != nil {
		log.Infof("action: apuestas_enviadas | result: fail | client_id: %v | error: %v", agency.client.config.ID, err)
		return
	}
	log.Infof("action: apuestas_enviadas | result: success | client_id: %v", agency.client.config.ID)
	if err := agency.AskForWinners(); err != nil {
		log.Infof("action: ask_winners | result: fail | client_id: %v | error: %v", agency.client.config.ID, err)
		return
	}
}

func (agency *BetAgency) SendBets(bets []*Bet) {
	serializedBets := serializeMultipleBets(bets)
	agency.client.SendMsg(serializedBets, true)
}

func (agency *BetAgency) AskForWinners() error {
	var err error

	message := fmt.Sprintf("winnners,%s", agency.client.config.ID)

	for {
		agency.client.createClientSocket()
		agency.client.SendMsg([]byte(message), false)
		
		res, err := agency.client.ReceiveAndSendConfirmation()
		if err != nil {
			break
		}
		if checkWinnersAnnouncementMsg(res) {
			winners := parseWinners(res)
			agency.AnnounceWinners(winners)
			break
		}
		agency.client.Shutdown()
		time.Sleep(100 * time.Millisecond)
	}
	agency.client.Shutdown()
	return err
}

func parseWinners(bytes []byte) []string {
	return strings.Split(string(bytes), WINNER_SEPARATOR)
}

func (agency *BetAgency) AnnounceWinners(winners []string) {
	length := len(winners)
	if len(winners[0]) == 0 {
		length = 0
	}
	log.Infof("action: winners_announced | result: success | client_id: %v | winners: %v", agency.client.config.ID, length)
}

func checkWinnersAnnouncementMsg(message []byte) bool {
	return message != nil && string(message) != WAITING_MESSAGE
}