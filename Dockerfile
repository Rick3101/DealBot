# Python 3.10 slim (webapp removed - now standalone project)
# Build version: 2025-11-03-v4 (backend only)
FROM python:3.10-slim

# Cria diretório da aplicação
WORKDIR /app

# Copia arquivos de dependências primeiro (melhor cache)
COPY requirements.txt .

# Instala dependências Python
RUN pip install --no-cache-dir -r requirements.txt

# Copia o resto dos arquivos
COPY . .

# Torna o script de entrypoint executável
RUN chmod +x /app/docker-entrypoint.sh

# Expõe a porta (Render usa variável $PORT)
EXPOSE 5000

# Usa script de entrypoint que lê $PORT do ambiente
ENTRYPOINT ["/app/docker-entrypoint.sh"]
