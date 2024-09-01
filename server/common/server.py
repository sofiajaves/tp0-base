import socket
import logging
import signal
from common.utils import process_message


MAX_MSG_SIZE = 4 
EXIT = "exit"

class Server:
    def __init__(self, port, listen_backlog):
        # Initialize server socket
        signal.signal(signal.SIGTERM, lambda signal, frame: self.stop())
        self._server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._server_socket.bind(('', port))
        self._server_socket.listen(listen_backlog)
        self.client_socket = None
        self._is_running = True

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
            while self._is_running and self.client_socket:
                msg_length = self.__receive_message_length()

                if msg_length == 0:
                    return

                msg = self.__safe_receive(msg_length).rstrip()
                if not msg:
                    logging.error("action: handle_client_connection | result: fail | error: client disconnected")
                    return
                self.__log_ip()
                self.__check_exit(msg)
                
                process_message(msg)

                self.__send_success_message()
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
        self.__safe_send("success")
        logging.info("action: send_success_message | result: success")

    def __send_error_message(self):
        self.__safe_send("error")
        logging.error("action: send_error_message | result: success")

    def __safe_send(self, message):
        total_sent = 0
        bytes_to_send = message.encode('utf-8')

        while total_sent < len(message):
            try: 
                n = self.client_socket.send(bytes_to_send[total_sent:])
                total_sent += n
            except socket.error as e:
                logging.error(f"action: safe_send | result: fail | error: {e}")
                break
            return

    def __safe_receive(self, buf_len):
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
    
    def __log_ip(self):
        addr = self.client_socket.getpeername()
        logging.info(f"action: log_ip | result: success | ip: {addr[0]}")

    def __check_exit(self, msg):
        if msg.decode('utf-8') == EXIT:
            logging.info("action: check_exit | result: success")
            raise socket.error("Client exited")
