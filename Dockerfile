# Imagem oficial do Playwright com Python — já inclui Chromium e todas as dependências
FROM mcr.microsoft.com/playwright/python:v1.44.0-jammy

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Instala o Chromium dentro do container
RUN playwright install chromium

COPY . .

# Porta dinâmica (Render injeta $PORT automaticamente)
ENV PORT=10000
EXPOSE 10000

CMD gunicorn --bind 0.0.0.0:$PORT --workers 1 --timeout 180 app:app
