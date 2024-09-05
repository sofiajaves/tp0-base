import csv
import datetime
import time
import logging
import socket

from common.bet import Bet

""" Bets storage location. """
STORAGE_FILEPATH = "./bets.csv"
""" Simulated winner number in the lottery contest. """
LOTTERY_WINNER_NUMBER = 7574

""" Checks whether a bet won the prize or not. """
def has_won(bet: Bet) -> bool:
    return bet.number == LOTTERY_WINNER_NUMBER

"""
Persist the information of each bet in the STORAGE_FILEPATH file.
Not thread-safe/process-safe.
"""
def store_bets(bets: list[Bet]) -> None:
    with open(STORAGE_FILEPATH, 'a+') as file:
        writer = csv.writer(file, quoting=csv.QUOTE_MINIMAL)
        for bet in bets:
            writer.writerow([bet.agency, bet.first_name, bet.last_name,
                             bet.document, bet.birthdate, bet.number])


"""
Loads the information all the bets in the STORAGE_FILEPATH file.
Not thread-safe/process-safe.
"""
def load_bets() -> list[Bet]:
    with open(STORAGE_FILEPATH, 'r') as file:
        reader = csv.reader(file, quoting=csv.QUOTE_MINIMAL)
        for row in reader:
            yield Bet(row[0], row[1], row[2], row[3], row[4], row[5])

def process_bets(msg: str):
    bets = []
    try:
        bets = Bet.deserialize_multiple_bets(msg)
        if bets:
            store_bets(bets)
    except Exception as e:
        logging.error(f"action: apuestas_recibidas | result: fail | error: {e}")
        return
    logging.info(f"action: apuestas_recibidas | result: success | cantidad: {len(bets)}")

def get_winner_bets_by_agency(bets: list[Bet], agency: str) -> list[Bet]:
    return list(filter(lambda bet: has_won(bet) and bet.agency == int(agency), bets))

def decode_utf8(msg: bytes) -> str:
    return msg.decode('utf-8')

def encode_string_utf8(msg: str) -> bytes:
    return msg.encode('utf-8')