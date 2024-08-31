package common

import (
	"io"
	"os"
	"strings"
	"bytes"
	"errors"
)

func readBets(file *os.File, id string, chunk_size int) ([]*Bet, error){
	buffer := make([]byte, chunk_size)

	n, err := file.Read(buffer)
	if n == 0 {
		return nil, errors.New("EOF")
	}
	if err != nil {
		if err == io.EOF {
			return nil, errors.New("EOF")
		}
		return nil, err
	}

	bets := string(bytes.Trim(buffer, "\r"), "\x00")
	bets_str := strings.Split(bets, "\n")

	if !strings.HasSuffix(bets, "\r") && !strings.HasSuffix(bets, "\n") {
		bets_str = bets_str[:len(bets_str)-1]

		offset := int64(len(bets)-strings.LastIndex(bets, "\n")-1)

		file.Seek(-offset, io.SeekCurrent)
	}
	return parseBets(bets_str, id), nil
}

func parseBets(bets_str, []string, id string) []*Bet {
	bets := make([]*Bet, len(bets_str))

	for i, bet_str := range bets_str {
		fields := strings.Split(bet_str, ",")
		if len(fields) != 5 {
			continue
		}

		bets[i] = NewBet(id, fields[0], fields[1], fields[2], fields[3], fields[4])
	}

	return bets
}