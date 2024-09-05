from multiprocessing import Lock, Process, Value
import socket
import logging
import signal
from common.client_handler import create_client_handler

MAX_MSG_SIZE = 4 
CONFIRMATION_MSG_LEN = 4
EXIT = "exit"
WINNERS = "winners"
SUCCESS_MSG = "succ"
ERROR_MSG = "err"
WAITING_MSG = "waiting"

class Server:
    def __init__(self, port, listen_backlog, clients):
        signal.signal(signal.SIGTERM, lambda signal, frame: self.stop())
        self._server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._server_socket.bind(('', port))
        self._server_socket.listen(listen_backlog)
        self.client_socket = None
        self._is_running = True
        self.clients = clients
        self.finished_clients = Value('i', 0)
        self.file_lock = Lock()
        self.processes = []

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
                if not client_socket:
                    continue
                process = Process(target=create_client_handler, args=(client_socket, self.file_lock, self.finished_clients, self.clients))
                if process:
                    self.processes.append(process)
                    process.start()
            except OSError as e:
                logging.error(f"action: run | result: fail | error: {e}")
                break
               

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
        logging.info("action: closing_active_socket | result: in_progress")
        self._server_socket.shutdown(socket.SHUT_RDWR)
        self._server_socket.close()
        self._server_socket = None
        logging.info("action: closing_active_socket | result: success")

        for process in self.processes:
            if process.is_alive():
                process.join()
                #process.terminate()

        logging.info("action: stop | result: success")

