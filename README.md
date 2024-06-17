# Sistema de Mensagens Instantâneas IRC

## Integrantes do Grupo
- Lucas Fidalgo Bitencourt - 2221061
- Mateus Batista Peixoto da Silva - 2221147
- José Guilherme - 2221010
- João Henrique de Oliveira Salles - 2221074

## Visão Geral do Sistema
Este sistema de mensagens instantâneas baseia-se no protocolo IRC (Internet Relay Chat) e consiste em dois componentes principais:

- **Servidor (servidor.py)**: Gerencia a comunicação entre clientes, distribuindo mensagens e mantendo informações sobre usuários e canais.
- **Cliente (cliente.py)**: Interface do usuário que permite a interação com o servidor, envio e recebimento de mensagens.

---

## Cliente (cliente.py)
O cliente permite que o usuário se conecte ao servidor IRC, envie comandos e receba mensagens.


### Comandos do Usuário
- **/connect <host>**: Conecta ao servidor IRC.
- **/nick <username>**: Define o apelido do usuário.
- **/disconnect <motivo>**: Desconecta do servidor IRC.
- **/quit <motivo>**: Sai do cliente IRC.
- **/join <canal>**: Entra em um canal. **Se o canal não existir ele é criado**
- **/leave <canal> <motivo>**: Sai de um canal.
- **/channel <canal>**: Define o canal atual ou lista os canais que está participando.
- **/list**: Lista os canais disponíveis.
- **/names <canal>**: Lista os usuários em um canal.
- **/msg <canal> <mensagem>**: Envia uma mensagem para um canal. Se o canal não for informado envia para o canal padrão se esse existir
- **/help**: Mostra a lista de comandos disponíveis.
- **ping <mensagem>**: Envia um ping para o servidor.

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


---

## Servidor (servidor.py)
O servidor é responsável por aceitar conexões de clientes, processar comandos e gerenciar a comunicação entre diferentes usuários.


### Funcionalidades

- **Iniciar o Servidor**
  - **Método**: `start()`
  - **Descrição**: Inicializa o servidor e começa a aceitar conexões de clientes em uma thread separada.

- **Aceitar Conexões**
  - **Método**: `accept_connections()`
  - **Descrição**: Escuta a porta especificada para novas conexões de clientes e cria uma thread para cada cliente conectado usando a classe Cliente e método run().

- **Processar Comandos**
  - **Métodos**: `receive_data(), process_commands(), handle_command(command)`
  - **Descrição**: Dentro da função run que roda em loop se espera receber dados com receive_data(), processar os dados e depois tratar os comandos com handle_command. A partir do handle_command() são usados outro métodos de acordo com o comando.



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

## Como Executar

### Servidor
Para iniciar o servidor, execute o seguinte comando no terminal:
```sh
python3 servidor.py
```


### Cliente
Para inicia o cliente, execute o seguinte comando no terminal:
```sh
python3 cliente.py

