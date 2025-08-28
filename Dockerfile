FROM python:3.11-slim

WORKDIR /app

# Copiar requirements primeiro para cache de camadas
COPY requirements.txt .

# Instalar dependências
RUN pip install --no-cache-dir -r requirements.txt

# Copiar todo o projeto
COPY . .

# Expor porta
EXPOSE 5000

# Comando para iniciar a aplicação
CMD ["python", "server.py"]
