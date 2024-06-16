# Define a imagem base
FROM python:3.9

# Define o diretório de trabalho dentro do container
WORKDIR /app

# Copia o código fonte para o diretório de trabalho
COPY . /app

# Instala as dependências do projeto
#RUN pip install -r requirements.txt

# Expõe a porta em que o servidor estará rodando
EXPOSE 6667

# Define o comando de inicialização do servidor
CMD ["python", "servidor.py"]