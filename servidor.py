import socket
import threading
from collections import deque


class Cliente:
    def __init__(self, connection, address, server):
        self.conn = connection
        self.addr = address
        self.server = server
        self.nick = None
        self.registered = False
        self.buffer = ""

    def send_data(self, message):
        try:
            self.conn.sendall(message.encode("utf-8"))
        except Exception as e:
            print(f"Erro ao enviar dados para {self.addr}: {e}")

    def receive_data(self):
        try:
            data = self.conn.recv(1024).decode("utf-8")
            if data:
                self.buffer += data
                if "\r\n" in self.buffer:
                    lines = self.buffer.split("\r\n")
                    self.buffer = lines[-1]
                    return lines[:-1]
            return []
        except Exception as e:
            print(f"Erro ao receber dados de {self.addr}: {e}")
            return []

    def process_commands(self, data):
        for command in data:
            print(f"Recebendo comando: {command}")  # Log do comando recebido
            self.handle_command(command)

    def handle_command(self, command):
        parts = command.split()
        cmd = parts[0].upper()
        if cmd == "NICK" and len(parts) > 1:
            self.handle_nick(parts[1])
        elif cmd == "USER" and len(parts) > 4:
            self.handle_user(parts[1], parts[4])
        elif cmd == "PING":
            self.send_data(f"PONG :{parts[1]}")
        elif cmd == "JOIN" and len(parts) > 1:
            self.handle_join(parts[1])
        elif cmd == "PART" and len(parts) > 1:
            self.handle_part(parts[1])
        elif cmd == "QUIT":
            self.handle_quit()
        elif cmd == "PRIVMSG" and len(parts) > 2:
            self.handle_privmsg(parts[1], " ".join(parts[2:]))
        elif cmd == "NAMES" and len(parts) > 1:
            self.handle_names(parts[1])
        else:
            self.send_data("ERROR :Unknown command\r\n")

    def handle_nick(self, nick):
        if not nick.isalnum() or len(nick) > 9:
            self.send_data(f"432 * {nick} :Erroneous Nickname\r\n")
        elif self.server.is_nick_available(nick):
            self.nick = nick
            self.send_data(f":server 001 {nick} :Welcome to the IRC Network {nick}\r\n")
            self.registered = True
        else:
            self.send_data(f"433 * {nick} :Nickname is already in use\r\n")

    def handle_user(self, username, realname):
        if self.registered:
            self.send_data(f":server 375 {self.nick} :- Message of the Day -\r\n")
            self.send_data(f":server 372 {self.nick} :- Welcome {self.nick}\r\n")
            self.send_data(f":server 376 {self.nick} :End of /MOTD command.\r\n")

    def handle_join(self, channel):
        self.server.add_to_channel(self, channel)
        self.send_data(f":{self.nick} JOIN :{channel}\r\n")
        self.server.broadcast_to_channel(
            channel, f":{self.nick} JOIN :{channel}\r\n", self
        )
        self.server.list_names(channel, self)

    def handle_part(self, channel):
        self.server.remove_from_channel(self, channel)
        self.send_data(f":{self.nick} PART {channel} :Leaving\r\n")
        self.server.broadcast_to_channel(
            channel, f":{self.nick} PART {channel} :Leaving\r\n", self
        )

    def handle_quit(self):
        self.server.remove_client(self)
        self.conn.close()
        print(f"Cliente {self.addr} desconectado.")

    def handle_privmsg(self, channel, message):
        self.server.broadcast_to_channel(
            channel, f":{self.nick} PRIVMSG {channel} :{message}\r\n", self
        )

    def handle_names(self, channel):
        self.server.list_names(channel, self)

    def run(self):
        print(f"Cliente {self.addr} conectado.")
        while True:
            data = self.receive_data()
            if data:
                self.process_commands(data)
            else:
                self.handle_quit()
                break


class Servidor:
    def __init__(self, port=6667):
        self.port = port
        self.clients = []
        self.channels = {}

    def is_nick_available(self, nick):
        return all(client.nick != nick for client in self.clients)

    def add_to_channel(self, client, channel):
        if channel not in self.channels:
            self.channels[channel] = deque()
        self.channels[channel].append(client)
        print(f"Cliente {client.addr} entrou no canal {channel}.")

    def remove_from_channel(self, client, channel):
        if channel in self.channels and client in self.channels[channel]:
            self.channels[channel].remove(client)
            if not self.channels[channel]:
                del self.channels[channel]
            print(f"Cliente {client.addr} saiu do canal {channel}.")

    def list_names(self, channel, client):
        if channel in self.channels:
            users = [c.nick for c in self.channels[channel] if c.nick is not None]
            client.send_data(
                f":{self.port} 353 {client.nick} = {channel} :{' '.join(users)}\r\n"
            )
            client.send_data(
                f":{self.port} 366 {client.nick} {channel} :End of /NAMES list.\r\n"
            )

    def broadcast_to_channel(self, channel, message, sender=None):
        if channel in self.channels:
            for client in self.channels[channel]:
                if client != sender:
                    client.send_data(message)

    def remove_client(self, client):
        for channel in list(self.channels.keys()):
            if client in self.channels[channel]:
                self.remove_from_channel(client, channel)
        self.clients.remove(client)
        print(f"Cliente {client.addr} foi removido.")

    def accept_connections(self):
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind(("", self.port))
        server_socket.listen(50)
        print(f"Servidor escutando na porta {self.port}...")

        try:
            while True:
                conn, addr = server_socket.accept()
                print(f"Conexão aceita de {addr}")
                client = Cliente(conn, addr, self)
                self.clients.append(client)
                threading.Thread(target=client.run).start()
        except Exception as e:
            print(f"Erro ao aceitar conexões: {e}")
        finally:
            server_socket.close()

    def start(self):
        threading.Thread(target=self.accept_connections).start()


def main():
    port = 6667  # Porta padrão do IRC
    server = Servidor(port)
    server.start()
    print("Servidor iniciado. Pressione Ctrl+C para parar.")
    try:
        while True:
            pass
    except KeyboardInterrupt:
        print("Servidor encerrado.")


if __name__ == "__main__":
    main()
