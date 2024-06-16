# Sistema de Mensagens Instantâneas IRC

## Integrantes do Grupo
- Lucas Fidalgo Bitencourt - 2221061
- Mateus Batista Peixoto da Silva - 2221147
- José Guilherme - 

## Visão Geral do Sistema
Este sistema de mensagens instantâneas baseia-se no protocolo IRC (Internet Relay Chat) e consiste em dois componentes principais:

- **Servidor (servidor.py)**: Gerencia a comunicação entre clientes, distribuindo mensagens e mantendo informações sobre usuários e canais.
- **Cliente (cliente.py)**: Interface do usuário que permite a interação com o servidor, envio e recebimento de mensagens.

---

## Servidor (servidor.py)
O servidor é responsável por aceitar conexões de clientes, processar comandos e gerenciar a comunicação entre diferentes usuários.

### Funcionalidades

- **Iniciar o Servidor**
  - **Método**: `start()`
  - **Descrição**: Inicializa o servidor e começa a aceitar conexões de clientes em uma thread separada.
  - **Utilização**: Executar o script `servidor.py` inicia o servidor na porta 6667.

- **Aceitar Conexões**
  - **Método**: `accept_connections()`
  - **Descrição**: Escuta a porta especificada para novas conexões de clientes e cria uma thread para cada cliente conectado.
  - **Utilização**: Internamente chamado pelo método `start()`.

- **Processar Comandos**
  - **Método**: `handle_command(command)`
  - **Descrição**: Processa comandos recebidos dos clientes e chama as funções apropriadas para cada comando.
  - **Utilização**: Internamente chamado ao receber dados de um cliente.

- **Adicionar Cliente ao Canal**
  - **Método**: `add_to_channel(client, channel)`
  - **Descrição**: Adiciona um cliente a um canal específico e notifica outros clientes do canal.
  - **Utilização**: Chamado quando um cliente envia o comando JOIN.

- **Remover Cliente do Canal**
  - **Método**: `remove_from_channel(client, channel, motivo)`
  - **Descrição**: Remove um cliente de um canal específico e notifica outros clientes do canal.
  - **Utilização**: Chamado quando um cliente envia o comando PART.

- **Broadcast de Mensagens**
  - **Método**: `broadcast_to_channel(channel, message, sender=None)`
  - **Descrição**: Envia uma mensagem para todos os clientes de um canal, exceto o remetente.
  - **Utilização**: Usado para comandos como PRIVMSG.

### Comandos IRC Implementados
- **NICK**: Define o apelido do usuário.
- **USER**: Define o nome real do usuário.
- **PING**: Verifica se o host ainda está conectado.
- **JOIN**: Permite que um usuário entre em um canal.
- **PART**: Permite que um usuário saia de um canal.
- **QUIT**: Desconecta o usuário do servidor.
- **PRIVMSG**: Envia mensagens privadas para um canal.
- **NAMES**: Lista os usuários de um canal.
- **LIST**: Lista os canais disponíveis.

---

## Cliente (cliente.py)
O cliente permite que o usuário se conecte ao servidor IRC, envie comandos e receba mensagens.

### Funcionalidades

- **Iniciar Cliente**
  - **Método**: `main()`
  - **Descrição**: Inicializa o cliente e começa a processar comandos do usuário.
  - **Utilização**: Executar o script `cliente.py` inicia o cliente.

- **Executar Cliente**
  - **Método**: `executar()`
  - **Descrição**: Loop principal que aguarda comandos do usuário e os processa.
  - **Utilização**: Chamado pelo método `main()`.

- **Conectar ao Servidor**
  - **Método**: `conectar(host, port=6667)`
  - **Descrição**: Estabelece uma conexão TCP com o servidor e envia os comandos NICK e USER.
  - **Utilização**: Comando do usuário `/connect <host>`.

- **Enviar Dados**
  - **Método**: `enviar_dados(msg)`
  - **Descrição**: Envia dados codificados ao servidor.
  - **Utilização**: Internamente chamado ao processar comandos.

- **Receber Dados**
  - **Método**: `receber_dados()`
  - **Descrição**: Recebe dados do servidor e processa os comandos recebidos.
  - **Utilização**: Internamente chamado em uma thread separada.

- **Processar Comandos do Servidor**
  - **Método**: `processar_comando(linha)`
  - **Descrição**: Processa os comandos recebidos do servidor.
  - **Utilização**: Internamente chamado ao receber dados.

### Comandos do Usuário
- **/nick <username>**: Define o apelido do usuário.
- **/connect <host>**: Conecta ao servidor IRC.
- **/disconnect <motivo>**: Desconecta do servidor IRC.
- **/quit <motivo>**: Sai do cliente IRC.
- **/join #<canal>**: Entra em um canal.
- **/leave #<canal> <motivo>**: Sai de um canal.
- **/channel #<canal>**: Define o canal atual ou lista os canais que está participando.
- **/list**: Lista os canais disponíveis.
- **/names #<canal>**: Lista os usuários em um canal.
- **/msg #<canal> <mensagem>**: Envia uma mensagem para um canal.
- **/help**: Mostra a lista de comandos disponíveis.
- **ping <mensagem>**: Envia um ping para o servidor.

---

## Como Executar

### Servidor
Para iniciar o servidor, execute o seguinte comando no terminal:
```sh
python3 servidor.py