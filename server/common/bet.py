import datetime
BET_MSG_SEPARATOR = "|"
BET_CHUNK_SEPARATOR = ";"

class Bet:
    def __init__(self, bet_agency: str, name: str, last_name: str, document: str, birthdate: str, number: str):
        """
        bet agency must be passed as int
        birthdate fmt: YYYY-MM-DD
        number must be passed ad int
        """
        self.agency = int(bet_agency)
        self.first_name = name
        self.last_name = last_name
        self.document = document
        self.birthdate = datetime.date.fromisoformat(birthdate)
        self.number = int(number)

    @staticmethod
    def deserialize(msg: str):
        """
        Deserialize a message into a Bet object
        """
        fields = msg.split(BET_MSG_SEPARATOR)
        if len(fields) != 6:
            return None
        bet_agency, name, last_name, document, birthdate, number = fields
       
        return Bet(bet_agency, name, last_name, document, birthdate, number)
        
    @staticmethod
    def deserialize_multiple_bets(message: str):
        bets = []
        for bet in message.split(BET_CHUNK_SEPARATOR):
            if not bet:
                continue
            deserialized_bet = Bet.deserialize(bet)
            if deserialized_bet:
                bets.append(deserialized_bet)
        return bets
