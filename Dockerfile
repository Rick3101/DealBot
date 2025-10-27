# Usa Python 3.10 with Node.js for webapp build
FROM python:3.10-slim

# Instala Node.js para build do webapp
RUN apt-get update && apt-get install -y \
    nodejs \
    npm \
    && rm -rf /var/lib/apt/lists/*

# Cria diretório da aplicação
WORKDIR /app

# Copia arquivos de dependências primeiro (melhor cache)
COPY requirements.txt .
COPY webapp/package*.json webapp/

# Instala dependências Python
RUN pip install --no-cache-dir -r requirements.txt

# Instala dependências Node.js
RUN cd webapp && npm install

# Copia o resto dos arquivos
COPY . .

# Build do webapp
RUN cd webapp && npm run build

# Copia script de entrypoint
COPY docker-entrypoint.sh /app/
RUN chmod +x /app/docker-entrypoint.sh

# Expõe a porta (Render usa variável $PORT)
EXPOSE 5000

# Usa script de entrypoint que lê $PORT do ambiente
ENTRYPOINT ["/app/docker-entrypoint.sh"]
