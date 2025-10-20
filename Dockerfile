# Dockerfile para Railway
# Usando Python 3.10 para melhor compatibilidade
FROM python:3.10-slim

# Definir diretório de trabalho
WORKDIR /app

# Copiar requirements e instalar dependências
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código da aplicação
COPY backend/ ./backend/

# Expor porta (Railway injeta PORT automaticamente)
EXPOSE 8080

# Comando de start
CMD cd backend && python app.py
