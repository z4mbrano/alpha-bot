# Dockerfile para Render.com
# Usando Python 3.10 para melhor compatibilidade
FROM python:3.10-slim

# Definir diretório de trabalho
WORKDIR /app

# Instalar dependências do sistema necessárias para PostgreSQL
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements e instalar dependências Python
COPY backend/requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código da aplicação
COPY backend/ ./backend/

# Criar diretórios necessários para persistência de SQLite (fallback)
RUN mkdir -p /opt/render/project/data

# Definir variáveis de ambiente
ENV PYTHONPATH=/app
ENV RENDER=true
ENV FLASK_ENV=production

# Expor porta (Render injeta PORT automaticamente)
EXPOSE $PORT

# Health check para Render
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:$PORT/api/health || exit 1

# Comando de start
CMD cd backend && python app.py
