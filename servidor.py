import socket
import threading
from collections import deque

# Mensagem do Dia (MOTD)
MOTD = [
    ":server 375 {nick} :- server Message of the Day -",
    ":server 372 {nick} :- Welcome to the IRC server",
    ":server 376 {nick} :End of /MOTD command.",
]


class Cliente:
    def __init__(self, connection, address, server):
        self.conn = connection
        self.addr = address
        self.server = server
        self.nick = None
        self.username = None
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
        elif cmd == "PING" and len(parts) > 1:
            self.send_data(f"PONG :{parts[1]}")
        elif cmd == "JOIN" and len(parts) > 1:
            if self.registered:
                self.handle_join(parts[1])
            else:
                self.send_data("ERROR :You need to register first\r\n")
        elif cmd == "PART" and len(parts) > 1:
            self.handle_part(parts[1])
        elif cmd == "QUIT":
            self.handle_quit()
        elif cmd == "PRIVMSG" and len(parts) > 2:
            self.handle_privmsg(parts[1], " ".join(parts[2:]))
        elif cmd == "NAMES" and len(parts) > 1:
            self.handle_names(parts[1])
        elif cmd == "LIST":
            self.handle_list()
        elif cmd == "MODE" and len(parts) > 1:
            self.handle_mode(parts[1])
        elif cmd == "WHO" and len(parts) > 1:
            self.handle_who(parts[1])
        else:
            self.send_data("ERROR :Unknown command\r\n")

    def handle_nick(self, nick):
        if not nick.isalnum() or len(nick) > 9:
            self.send_data(f"432 * {nick} :Erroneous Nickname\r\n")
        elif self.server.is_nick_available(nick):
            self.nick = nick
            self.send_data(f":server 001 {nick} :Welcome to the IRC Network {nick}\r\n")
            self.check_registration()
        else:
            self.send_data(f"433 * {nick} :Nickname is already in use\r\n")

    def handle_user(self, username, realname):
        self.username = username
        self.send_data(f":server 375 {self.nick} :- server Message of the Day -\r\n")
        self.send_data(f":server 372 {self.nick} :- Welcome to the IRC server\r\n")
        self.send_data(f":server 376 {self.nick} :End of /MOTD command.\r\n")
        self.check_registration()

    def check_registration(self):
        if self.nick and self.username:
            self.registered = True
            self.send_data(f":server 001 {self.nick} :Welcome {self.nick}\r\n")

    def handle_join(self, channel):
        self.server.add_to_channel(self, channel)
        self.send_data(f":{self.nick} JOIN :{channel}\r\n")
        self.server.broadcast_to_channel(
            channel, f":{self.nick} JOIN :{channel}\r\n", self
        )
        self.server.list_names(channel, self)

    def handle_part(self, channel):
        if channel in self.server.channels and self in self.server.channels[channel]:
            self.server.remove_from_channel(self, channel)
            self.send_data(f":{self.nick} PART {channel} :Leaving\r\n")
            self.server.broadcast_to_channel(
                channel, f":{self.nick} PART {channel} :Leaving\r\n", self
            )
        else:
            self.send_data(f"442 {self.nick} {channel} :You're not on that channel\r\n")

    def handle_quit(self):
        self.server.remove_client(self)
        self.conn.close()
        print(f"Cliente {self.addr} desconectado.")

    def handle_privmsg(self, channel, message):
        self.server.broadcast_to_channel(
            channel, f":{self.nick} PRIVMSG {channel} :{message}\r\n", self
        )

    def handle_names(self, channel):
        if channel in self.server.channels:
            users = [
                c.nick for c in self.server.channels[channel] if c.nick is not None
            ]
            self.send_data(
                f":{self.server.port} 353 {self.nick} = {channel} :{' '.join(users)}\r\n"
            )
            self.send_data(
                f":{self.server.port} 366 {self.nick} {channel} :End of /NAMES list.\r\n"
            )
        else:
            self.send_data(f"403 {self.nick} {channel} :No such channel\r\n")

    def handle_list(self):
        for channel, clients in self.server.channels.items():
            self.send_data(f":server 322 {self.nick} {channel} {len(clients)} :\r\n")
        self.send_data(f":server 323 {self.nick} :End of /LIST\r\n")

    def handle_mode(self, channel):
        # Placeholder response for MODE command
        self.send_data(f":server 324 {self.nick} {channel} +nt\r\n")

    def handle_who(self, channel):
        if channel in self.server.channels:
            for client in self.server.channels[channel]:
                self.send_data(
                    f":server 352 {self.nick} {channel} {client.username} {client.addr[0]} server {client.nick} H :0 {client.username}\r\n"
                )
            self.send_data(f":server 315 {self.nick} {channel} :End of /WHO list.\r\n")
        else:
            self.send_data(f"403 {self.nick} {channel} :No such channel\r\n")

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
        self.broadcast_to_channel(
            channel, f":{client.nick} JOIN :{channel}\r\n", client
        )

    def remove_from_channel(self, client, channel):
        if channel in self.channels and client in self.channels[channel]:
            self.channels[channel].remove(client)
            if not self.channels[channel]:
                del self.channels[channel]
            print(f"Cliente {client.addr} saiu do canal {channel}.")
            self.broadcast_to_channel(
                channel, f":{client.nick} PART {channel} :Leaving\r\n", client
            )

    def list_names(self, channel, client):
        if channel in self.channels:
            users = [c.nick for c in self.channels[channel] if c.nick is not None]
            client.send_data(
                f":{self.port} 353 {client.nick} = {channel} :{' '.join(users)}\r\n"
            )
            client.send_data(
                f":{self.port} 366 {client.nick} {channel} :End of /NAMES list.\r\n"
            )
        else:
            client.send_data(f"403 {client.nick} {channel} :No such channel\r\n")

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
