# Usa Python 3.10 with Node.js for webapp build
# Build version: 2025-10-26-v2 (force rebuild with polyfill)
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

# Instala dependências Python
RUN pip install --no-cache-dir -r requirements.txt

# Copia o resto dos arquivos (incluindo webapp completo)
COPY . .

# Torna o script de entrypoint executável
RUN chmod +x /app/docker-entrypoint.sh

# Instala dependências Node.js e build webapp
WORKDIR /app/webapp
# Remove any existing dist and node_modules to ensure clean build
RUN rm -rf dist node_modules
RUN npm install --no-cache
RUN npm run build

# Volta para diretório raiz
WORKDIR /app

# Expõe a porta (Render usa variável $PORT)
EXPOSE 5000

# Usa script de entrypoint que lê $PORT do ambiente
ENTRYPOINT ["/app/docker-entrypoint.sh"]
