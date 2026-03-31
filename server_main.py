import socket
import threading
import configparser
from concurrent.futures import ThreadPoolExecutor
from ClientHandler import MDVRClientHandler
from logger import Logger


class MDVRServer:
    def __init__(self, config_file='mdvr_config.ini', max_workers=500):
        """
        Initialize the MDVR Server.
        :param config_file: Path to the configuration file.
        :param max_workers: Maximum number of threads in the thread pool.
        """
        self.config_file = config_file
        self.config = self.read_config()
        self.port = int(self.config.get('Server', 'Port', fallback=6623))
        self.log_dir = self.config.get('Logging', 'log_dir')
        self.deletion_days = self.config.get('Logging', 'deletion_days')
        self.logger = Logger()
        self.server_socket = None
        self.thread_pool = ThreadPoolExecutor(max_workers=max_workers)
        self.clients = []
        self.shutdown_event = threading.Event()

    def read_config(self):
        """
        Read the server configuration from the config file.
        :return: ConfigParser object with configuration settings.
        """
        config = configparser.ConfigParser()
        try:
            config.read(self.config_file)
            return config
        except Exception as e:
            self.logger.log("server_file_error", f"Error reading config file: {e}", log_level="ERROR")
            raise

    def start_server(self):
        """
        Start the MDVR server to accept client connections.
        """
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind(('0.0.0.0', self.port))
            self.server_socket.listen(1000)
            print(f"MDVR Server started and listening on port {self.port}")

            while not self.shutdown_event.is_set():
                try:
                    client_socket, addr = self.server_socket.accept()
                    print(f"Accepted connection from {addr}")
                    handler = MDVRClientHandler(client_socket, addr, self)
                    self.clients.append(handler)
                    self.thread_pool.submit(handler.run)
                except socket.error as e:
                    self.logger.log("server_file_error", f"Socket error while accepting connection: {e}", log_level="ERROR")
        except Exception as e:
            self.logger.log("server_file_error", f"An exception occurred while starting the MDVR server: {e}", log_level="ERROR")
        finally:
            self.stop_server()

    def stop_server(self):
        """
        Stop the MDVR server and close all client connections.
        """
        print("Stopping the MDVR Server...")
        self.shutdown_event.set()
        for client in self.clients:
            client.stop()
        self.thread_pool.shutdown(wait=False)
        if self.server_socket:
            self.server_socket.close()
        print("MDVR Server stopped.")

    def run(self):
        """
        Run the MDVR server in a separate thread.
        """
        try:
            server_thread = threading.Thread(target=self.start_server, daemon=True)
            server_thread.start()
            server_thread.join()  # Keep the main thread running
        except KeyboardInterrupt:
            self.logger.log_data("server_file_error", f"Shutdown signal received. Stopping the server...")
            self.stop_server()


if __name__ == "__main__":
    # Run the MDVR server
    mdvr_server = MDVRServer()
    mdvr_server.run()
