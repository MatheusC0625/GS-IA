# Imagem da API Flask para publicar no Render.
# Copia só o que a API usa: o código (api/) e os modelos treinados (modelos/).
FROM python:3.13-slim

WORKDIR /app

# MALLOC_ARENA_MAX=2 reduz o uso de memória do Python (plano gratuito do Render: 512 MB)
ENV PYTHONUNBUFFERED=1 \
    MALLOC_ARENA_MAX=2

# instala as dependências primeiro (o Docker reaproveita essa camada se o código mudar)
COPY api/requirements.txt api/requirements.txt
RUN pip install --no-cache-dir -r api/requirements.txt

COPY modelos/ modelos/
COPY api/ api/

WORKDIR /app/api
EXPOSE 5000

# o Render informa a porta na variável PORT; 1 worker para caber na memória
CMD gunicorn --bind 0.0.0.0:${PORT:-5000} --workers 1 --threads 2 --timeout 120 app:app
