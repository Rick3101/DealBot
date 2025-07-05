# Usa Python 3.10
FROM python:3.10-slim

# Cria diretório da aplicação
WORKDIR /app

# Copia todos os arquivos
COPY . .

# Instala dependências
RUN pip install --no-cache-dir -r requirements.txt

# Expõe a porta padrão do Flask
EXPOSE 5000

# Comando para iniciar o bot
CMD ["python", "app.py"]
