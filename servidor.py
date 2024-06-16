import socket
import threading
from collections import deque
import re
import time

# Mensagem do Dia (MOTD)
MOTD = "Imagine uma mensagem inspiracional aqui kk (:"

class Cliente:
    
    def __init__(self, connection, address, server):
        self.conn = connection
        self.addr = address
        self.server = server
        self.nick = None
        self.username = None
        self.realname = None
        self.registered = False
        self.buffer = ""
        self.actual_channel = None
    
    # Função que roda em loop para receber e processar comandos do cliente
    def run(self):
        print(f"Cliente {self.addr} conectado.")
        try:
            ping_thread = threading.Thread(target=self.send_ping)
            ping_thread.start()
            
            while True:
                data = self.receive_data()
                if data:
                    self.process_commands(data)
                else:
                    self.handle_quit()
                    break
        except Exception as e:
            print(f"Erro ao processar dados de {self.addr}: {e}")
        finally:
            self.handle_quit()
    
    # Auxilia a função run() a receber dados de comando do cliente 
    def receive_data(self):
        try:
            data = self.conn.recv(1024).decode("utf-8")
            if data:
                self.buffer += data
                if "\r\n" in self.buffer:
                    lines = self.buffer.split("\r\n")
                    self.buffer = lines[-1] # Armazenando linha incompleta para processamento futuro
                    return lines[:-1] # Retornando lista de linhas completas para processamento
            return []
        except Exception as e:
            print(f"Erro ao receber dados de {self.addr}: {e}")
            return []
     
    # Processa linhas recebidas do cliente  
    def process_commands(self, data):
        # Iterando sobre cada linha de comando recebida
        for command in data:
            print(f"Recebendo comando: {command}")  # Log do comando recebido
            self.handle_command(command) 
    
    # Divide cada linha de comando em partes e chama a função correspondente
    def handle_command(self, command):
        parts = command.split()
        cmd = parts[0].upper()
        if cmd == "NICK" and len(parts) > 1:
            self.handle_nick(parts[1])
        elif cmd == "USER" and len(parts) > 4:
            realname = " ".join(parts[4:])
            self.handle_user(parts[1], realname)
        elif cmd == "PING" and len(parts) > 1:
            mensagem = " ".join(parts[1:]) 
            self.handle_ping(mensagem)
        elif cmd == "PONG":
            self.handle_pong(" ".join(parts[0:]))
        elif cmd == "JOIN" and len(parts) > 1:
            if self.registered:
                self.handle_join(parts[1])
            else:
                self.send_data("ERRO : Necessário estar registrado\r\n")
        elif cmd == "PART" and len(parts) > 1:
            motivo = " ".join(parts[2:]) if len(parts) > 2 else ""
            self.handle_part(parts[1], motivo)
        elif cmd == "QUIT":
            motivo = " ".join(parts[1:]) if len(parts) > 1 else ""
            self.handle_quit(motivo)
        elif cmd == "PRIVMSG" and len(parts) > 2:
            if self.registered:
                mensagem = " ".join(parts[2:])
                self.handle_privmsg(parts[1], mensagem)
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
        #if not nick.isalnum() or len(nick) > 9:
        if not re.match("^[A-Za-z][A-Za-z0-9_]{0,8}$", nick):
            self.send_data(f"432 * {nick} :Erroneous Nickname\r\n")
        
        elif self.server.is_nick_available(nick):
            old_nick = self.nick
            self.nick = nick
            if old_nick:
                self.send_data(f":{old_nick} NICK {nick}\r\n")
                self.server.broadcast_to_channel(self.channel, f":{old_nick} NICK {nick}\r\n", self)
            self.check_registration() # Verifica se o cliente já registrou um nick e um username
        else:
            self.send_data(f"433 * {nick} :Nickname is already in use\r\n")

    def handle_user(self, username, realname):
        self.realname = realname
        self.check_registration()

    def check_registration(self):
        if self.nick and self.realname:
            self.registered = True
            self.send_data(f":001 {self.nick} :Welcome to the Internet Relay Network {self.nick}\r\n")
            self.send_data(f":server 375 {self.nick} :- {self.server.host} Message of the Day -\r\n")
            self.send_data(f":server 372 {self.nick} :- {MOTD}\r\n")
            self.send_data(f":server 376 {self.nick} :End of /MOTD command.\r\n")

    def handle_join(self, channel):
        self.server.add_to_channel(self, channel)
        self.actual_channel = channel
        

    def handle_part(self, channel, motivo=""):
        self.server.remove_from_channel(self, channel, motivo)
        
    def handle_quit(self, motivo=""):
        self.server.remove_client(self, motivo)
        self.conn.close()
        
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
                f":{self.server.host} 353 {self.nick} = {channel} :{' '.join(users)}\r\n"
            )
            self.send_data(
                f":{self.server.host} 366 {self.nick} {channel} :End of /NAMES list.\r\n"
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

    def handle_ping(self, message):
        self.send_data(f"PONG :{message}\r\n")

    def send_data(self, message):
        try:
            self.conn.sendall(message.encode("utf-8"))
        except Exception as e:
            print(f"Erro ao enviar dados para {self.addr}: {e}")
            
    def send_ping(self):
        while True:
            try:
                self.send_data("PING :server\r\n")
                time.sleep(30)  # Envia PING a cada 60 segundos
            except Exception as e:
                print(f"Erro ao enviar PING: {e}")
                break
    
    def handle_pong(self, resposta):
        print(resposta)
        
class Servidor:
    
    # Inicializando servidor com porta padrão 6667 e listas de clientes e canais
    def __init__(self, port=6667):
        self.port = port
        self.host = None
        self.clients = []
        self.channels = {}

    
    # Inicializando servidor em uma thread na função accept_connections

    def start(self):
        threading.Thread(target=self.accept_connections).start()


    # Função que roda em loop para aceitar conexões de clientes até que o servidor seja encerrado
    # Adiciona clientes na lista de clientes (atributo da classe Servidor)
    # Para cada conexão cria objeto da classe Cliente e uma nova thread usando Cliente.run()
    def accept_connections(self):
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind(("", self.port))
        server_socket.listen(50)
        self.host = socket.gethostname()
        
        
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
            

    def is_nick_available(self, nick):
        return all(client.nick != nick for client in self.clients)

    def add_to_channel(self, client, channel):
        if channel not in self.channels:
            self.channels[channel] = deque()
            self.channels[channel].append(client)
            client.send_data(f":{self.host} 403 {client.nick} #{channel} :No such channel\r\n")
            
        else:
            if client in self.channels[channel]:
                client.send_data(f":{self.host} 442 {client.nick} {channel} :You're already on that channel\r\n")
            else:
                self.channels[channel].append(client)
                client.send_data(f":{client.nick} JOIN :{channel}\r\n")
                self.broadcast_to_channel(channel, f":{client.nick} JOIN :{channel}\r\n", client)
                self.list_names(channel, client)

    def remove_from_channel(self, client, channel, motivo):
        if channel in self.channels and client in self.channels[channel]:
            self.channels[channel].remove(client)
            client.send_data(f":{client.nick} PART {channel} {motivo}\r\n")
            if not self.channels[channel]:
                del self.channels[channel]
            self.broadcast_to_channel(
                channel, f":{client.nick} PART {channel} {motivo}\r\n", client
            )
        else:
            client.send_data(f"{self.host} 442 {client.nick} {channel} :You're not on that channel\r\n")

    def list_names(self, channel, client):
        if channel in self.channels:
            users = [c.nick for c in self.channels[channel] if c.nick is not None]
            client.send_data(
                f":{self.host} 353 {client.nick} = {channel} :{' '.join(users)}\r\n"
            )
            client.send_data(
                f":{self.host} 366 {client.nick} {channel} :End of /NAMES list.\r\n"
            )
        else:
            client.send_data(f"403 {client.nick} {channel} :No such channel\r\n")

    def broadcast_to_channel(self, channel, message, sender=None):
        if channel in self.channels:
            for client in self.channels[channel]:
                if client != sender:
                    client.send_data(message)

    def remove_client(self, client, motivo):
        for channel in list(self.channels.keys()):
            if client in self.channels[channel]:
                self.channels[channel].remove(client)
        if client in self.clients:
            self.clients.remove(client)
        try:
            client.send_data(f":{client.nick} QUIT {motivo} \r\n")
        except Exception as e:
            print(f"Erro ao enviar dados para {client.addr}: {e}")
        


def main():
    port = 6667  # Porta padrão do IRC
    server = Servidor(port) # Inicializando classe Servidor
    server.start() # Inicializando servidor
    print("Servidor iniciado. Pressione Ctrl+C para parar.")
    try:
        while True:
            pass
    except KeyboardInterrupt:
        print("Servidor encerrado.")


if __name__ == "__main__":
    main()
