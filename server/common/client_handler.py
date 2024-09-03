import socket
import logging
import signal
from common.utils import decode_utf8, encode_string_utf8, load_bets, process_bets, get_winner_bets_by_agency

MAX_MSG_SIZE = 4 
CONFIRMATION_MSG_LEN = 4
EXIT = "exit"
WINNERS = "winners"
SUCCESS_MSG = "succ"
ERROR_MSG = "err"
WAITING_MSG = "waiting"

class ClientHandler:
    def __init__(self, client_socket, file_lock, finished_clients, clients):
        signal.signal(signal.SIGTERM, lambda signal, frame: self.stop())

        self.file_lock = file_lock
        self.client_socket = client_socket
        self.finished_clients = finished_clients
        self.clients = clients
        self._is_running = True

    def __receive_message_length(self):
        try: 
            msg_len = int.from_bytes(self.__safe_receive(MAX_MSG_SIZE).rstrip(), "little")
            logging.info(f"action: receive_message_length | result: success | msg_len: {msg_len}")
            self.__send_success_message()
            return msg_len
        except socket.error as e:
            logging.error(f"action: receive_message_length | result: fail | error: {e}")
            raise e
        except Exception as e:
            self.__send_error_message()
            logging.error("action: receive_message_length | result: fail | error: {e}")
            return 0
        
    def handle_client_connection(self):
        """
        Read message from a specific client socket and closes the socket

        If a problem arises in the communication with the client, the
        client socket will also be closed
        """
        try:
            self.client_socket.settimeout(10)
            while self._is_running and self.client_socket:
                msg_length = self.__receive_message_length()

                if msg_length == 0:
                    return

                msg = self.__safe_receive(msg_length)
                if msg is None:  # Verifica si se recibió None, lo que indica un error
                    logging.error("action: handle_client_connection | result: fail | error: no message received")
                    return

                msg = msg.rstrip()
                if not msg:
                    logging.error("action: handle_client_connection | result: fail | error: client disconnected")
                    return
                self.__log_ip()
                self.__check_exit(msg)
                
                self.process_message(msg)
        except socket.timeout:
            self.__send_error_message()
            logging.error("action: handle_client_connection !!! | result: fail | error: timeout")
        except OSError as e:
            self.__send_error_message()
            logging.error(f"action: receive_message | result: fail | error: {e}")
        finally:
            self.__close_client_connection()

    def __close_client_connection(self):
        logging.info('action: close_client_connection | result: in_progress')
        with self.finished_clients.get_lock():
            self.finished_clients.value += 1
        
        self.client_socket.shutdown(socket.SHUT_RDWR)
        self.client_socket.close()
        self.client_socket = None
        logging.info('action: close_client_connection | result: success')

    def __send_success_message(self):
        self.__safe_send(encode_string_utf8(SUCCESS_MSG))
        logging.info("action: send_success_message | result: success")

    def __send_error_message(self):
        self.__safe_send(encode_string_utf8(ERROR_MSG))
        logging.error("action: send_error_message | result: success")

    def __check_exit(self, msg):
        if msg.decode('utf-8') == EXIT:
            raise socket.error("Client disconnected")
    
    def __safe_send(self, bytes_to_send):
        total_sent = 0

        while total_sent < len(bytes_to_send):
            n = self.client_socket.send(bytes_to_send[total_sent:])
            total_sent += n
        return

    def __safe_receive(self, buf_len: int):
        msg = 0
        buffer = bytes()
        while msg < buf_len:
            try:
                message = self.client_socket.recv(buf_len - msg)
                if not message:
                    logging.info(f"action: safe_receive | result: client disconnected")
                    self.__close_client_connection()
                    return None
                buffer += message
                msg += len(message)
            except socket.error as e:
                logging.error(f"action: safe_receive | result: fail | error: {e}")
                self.__close_client_connection()
                return None
        return buffer
    
    def process_message(self, msg: bytes):
        message = decode_utf8(msg)
        split_msg = message.split(",")
        if msg == EXIT:
            raise socket.error("Client disconnected")
        elif len(split_msg) == 2 and split_msg[0] == WINNERS:
            self.__send_winners(split_msg[1])
        else:
            process_bets(message)
            self.__send_success_message()

    def __send_winners(self, agency: str):
        if self.finished_clients.value < self.clients:
            self.__send_and_wait_confirmation(encode_string_utf8(WAITING_MSG))
            return
        elif self.finished_clients == 5:
            logging.info("action: sorteo | result: success")
        bets = load_bets()
        winner_bets = get_winner_bets_by_agency(bets, agency)
        docs = map(lambda bet: bet.document, winner_bets)
        response = ",".join(docs)
        self.__send_and_wait_confirmation(encode_string_utf8(response))

    def __send_and_wait_confirmation(self, msg: bytes):

        self.__safe_send(len(msg).to_bytes(MAX_MSG_SIZE, "little"))
        if decode_utf8(self.__safe_receive(CONFIRMATION_MSG_LEN)) != SUCCESS_MSG:
            raise socket.error("Client did not confirm message reception")
        
        self.__safe_send(msg)
        if decode_utf8(self.__safe_receive(CONFIRMATION_MSG_LEN)) != SUCCESS_MSG:
            raise socket.error("Client did not confirm message reception")

    def __log_ip(self):
        addr = self.client_socket.getpeername()
        logging.info(f"action: log_ip | result: success | ip: {addr[0]}")


    def stop(self):
        logging.info("action: stop | result: in_progress")
        self._is_running = False
        self._server_socket.close()
        
        self.__close_client_connection()
        logging.info("action: stop | result: success")

def create_client_handler(client_socket, file_lock, finished_clients, clients):
    handler = ClientHandler(client_socket, file_lock, finished_clients, clients)
    handler.handle_client_connection