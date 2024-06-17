import signal
import socket
import threading
import time


class Cliente:
    def __init__(self):
        self.conectado = False
        self.socket = None
        self.nick = None
        self.buffer = ""
        self.current_channel = None
        self.channels = set()

        # Exceção para alarme de tempo (não alterar esta linha)
        signal.signal(signal.SIGALRM, self.exception_handler)

    def executar(self):
        print("Cliente IRC iniciado!")
        
        while True:
            
            try:
                cmd = input()
            except Exception as e:
                print(f"Erro ao receber comando: {e}")
                continue
            
            partes = cmd.split()
            comando = partes[0].lower()

            if comando == "/nick":
                if len(partes) >= 2:
                    self.nick_command(partes[1])
                else:
                    print("Uso: /nick <username>")
            
            elif comando == "/connect":
                if len(partes) >= 2:
                    self.conectar(partes[1])
                else:
                    print("Uso: /connect <ip>")
            elif comando == "/disconnect":
                motivo = " ".join(partes[1:]) if len(partes) > 1 else ""
                self.quit_command(motivo)
            elif comando == "/quit":
                motivo = " ".join(partes[1:]) if len(partes) > 1 else ""
                self.quit_command(motivo)
                break
            elif comando == "/join":
                if len(partes) >= 2:
                    self.join_command(partes[1])
                else:
                    print("Uso: /join <canal>")
            elif comando == "/leave":
                if len(partes) >= 2:
                    self.part_command(partes[1], " ".join(partes[2:]))
                else:
                    print("Uso: /leave <canal> <motivo>")
            elif comando == "/channel":
                if len(partes) >= 2:
                    if partes[1] in self.channels:
                        self.current_channel = partes[1]
                        print(f"Canal atual: {self.current_channel}")
                    else:
                        print("Você não está neste canal")
                else:
                    print(f"Canais: {', '.join(self.channels)}")
            elif comando == "/list":
                if len(partes) >= 2:
                    self.list_command(partes[1])
                else:
                    print("Uso: /list <canal>")
            elif comando == "/names":
                if len(partes) >= 2:
                    self.names_command(partes[1])
                elif self.current_channel:
                    self.names_command(self.current_channel)
                else:
                    print("Uso: /names <canal>")
            elif comando == "/msg":
                if len(partes) >= 3:
                    self.privmsg_command(partes[1], " ".join(partes[2:]))
                elif self.current_channel and len(partes) >= 2:
                    self.privmsg_command(self.current_channel, " ".join(partes[1:]))
                else:
                    print("Uso: /msg <canal> <mensagem> ou /msg <mensagem>")
    
            elif comando == "/help":
                self.mostrar_ajuda()
            
            elif comando == "ping":
                self.send_ping(" ".join(partes[1:]))
            else:
                print("Comando não reconhecido. Digite /help para ver os comandos disponíveis.")
                #if self.current_channel:
                #    self.privmsg_command(self.current_channel, " ".join(partes[0:]))
                #else:
                #    print("Comando não reconhecido. Digite /help para ver os comandos disponíveis.")


    def check_server_messages(self):
        if self.conectado:
            data = self.receber_dados()
            if data:
                self.processar_comando(data)
    # Tratamento de exceção para alarme de tempo (não alterar este método)
    def exception_handler(self, signum, frame):
        raise Exception("EXCEÇÃO (timeout)")

    def conectar(self, host, port=6667):
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((host, port))
            self.conectado = True
            threading.Thread(target=self.receber_dados).start()

            # Solicita nick e user do usuário
            nick = input("Digite seu nick: ")
            realname = input("Digite seu nome real: ")

            self.nick_command(nick)
            self.user_command(nick, realname)
            
        except Exception as e:
            print(f"Erro ao conectar ao servidor: {e}")
            self.conectado = False

    def enviar_dados(self, msg):
        if self.conectado:
            try:
                self.socket.sendall(f"{msg}\r\n".encode("utf-8"))
            except Exception as e:
                print(f"Erro ao enviar dados: {e}")

    def receber_dados(self):
        while self.conectado:
            try:
                data = self.socket.recv(1024).decode("utf-8")
                if data:
                    self.buffer += data
                    while "\r\n" in self.buffer:
                        linha, self.buffer = self.buffer.split("\r\n", 1)
                        self.processar_comando(linha)
                else:
                    self.conectado = False
            except Exception as e:
                print(f"Erro ao receber dados: {e}")
                self.conectado = False

    def processar_comando(self, linha):
        parts = linha.split()
        if parts[0] == "PING":
            mensagem = parts[1]
            self.pong_resp(mensagem)
        else:
            print(linha)
        

    def nick_command(self, username):
        self.nick = username
        self.enviar_dados(f"NICK {username}")

    def user_command(self, username, realname):
        self.enviar_dados(f"USER {username} 0 = {realname}")

    def join_command(self, canal):
        self.enviar_dados(f"JOIN {canal}")
        self.channels.add(canal)
        self.current_channel = canal

    def part_command(self, canal, motivo):
        self.enviar_dados(f"PART {canal} {motivo}")
        self.channels.discard(canal)
        if self.current_channel == canal:
            self.current_channel = None

    def quit_command(self, motivo):
        self.enviar_dados(f"QUIT {motivo}")
        self.conectado = False
        self.socket.close()
             

    def privmsg_command(self, canal, mensagem):
        self.enviar_dados(f"PRIVMSG {canal} {mensagem}")

    def names_command(self, canal):
        self.enviar_dados(f"NAMES {canal}")

    def list_command(self, canal):
        self.enviar_dados(f"LIST {canal}")

    def pong_resp(self, msg):
        self.enviar_dados(f"PONG {msg}")

    def send_ping(self, mensagem):
        self.enviar_dados(f"PING {mensagem}")

    def mostrar_ajuda(self):
        print(
            """
Comandos disponíveis:
/nick <username>        - Define o nickname do usuário
/connect <host>         - Conecta ao servidor IRC
/disconnect <motivo>    - Desconecta do servidor IRC
/quit <motivo>          - Sai do cliente IRC
/join <canal>          - Entra em um canal
/leave <canal> <motivo> - Sai de um canal
/channel <#canal>       - Define o canal atual ou lista os canais que está participando
/list                   - Lista os canais disponíveis
/names <canal>         - Lista os usuários em um canal
/msg <canal> <mensagem> - Envia uma mensagem para um canal
/help                   - Mostra esta mensagem de ajuda
            """
        )


def main():
    c = Cliente()
    c.executar()


if __name__ == "__main__":
    main()
