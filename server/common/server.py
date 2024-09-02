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

class Server:
    def __init__(self, port, listen_backlog, clients):
        # Initialize server socket
        signal.signal(signal.SIGTERM, lambda signal, frame: self.stop())
        self._server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._server_socket.bind(('', port))
        self._server_socket.listen(listen_backlog)
        self.client_socket = None
        self._is_running = True
        self.clients = clients
        self.finished_clients = 0

    def run(self):
        """
        Dummy Server loop

        Server that accept a new connections and establishes a
        communication with a client. After client with communucation
        finishes, servers starts to accept new connections again
        """

        while self._is_running:
            try:
                client_socket = self.__accept_new_connection()
                if client_socket:
                    self.client_socket = client_socket
                    self.__handle_client_connection()
            except OSError as e:
                if client_socket is None:
                    logging.error(f"action: run | result: client disconnected")
                    break
                else: 
                    logging.error(f"action: run | result: fail | error: {e}")
                    self.__close_client_connection()
                    break

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
        

    def __handle_client_connection(self):
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
        if self.client_socket:
            try:
                    self.client_socket.shutdown(socket.SHUT_RDWR)
            except OSError as e:
                    if self.client_socket is None:
                        logging.error(f'action: close_client_connection | result: fail | error: client disconnected')
                    logging.error(f'action: close_client_connection | result: fail | error: {e}')
            finally:
                self.finished_clients += 1
                self.client_socket.close()
                self.client_socket = None
                logging.info('action: close client connection | result: success')

    def __accept_new_connection(self):
        """
        Accept new connections

        Function blocks until a connection to a client is made.
        Then connection created is printed and returned
        """

        # Connection arrived
        logging.info('action: accept_connections | result: in_progress')
        if not self._is_running or self._server_socket.fileno() == -1:
            return None
        try:
            c, addr = self._server_socket.accept()
            logging.info(f'action: accept_connections | result: success | ip: {addr[0]}')
            return c
        except OSError as e:
            logging.info(f'action: accept_connections | result: fail | error: {e}')
            return None
        
    def stop(self):
        logging.info("action: stop | result: in_progress")
        self._is_running = False
        self._server_socket.close()
        
        self.__close_client_connection()
        logging.info("action: stop | result: success")

    def __send_success_message(self):
        self.__safe_send(encode_string_utf8(SUCCESS_MSG))
        logging.info("action: send_success_message | result: success")

    def __send_error_message(self):
        self.__safe_send(encode_string_utf8(ERROR_MSG))
        logging.error("action: send_error_message | result: success")
    
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
        if self.finished_clients < self.clients:
            logging.debug("clientes: %d", self.clients)
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

    def __check_exit(self, msg):
        if msg.decode('utf-8') == EXIT:
            logging.info("action: check_exit | result: success")
            raise socket.error("Client exited")
