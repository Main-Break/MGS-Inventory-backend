# Imagem de deploy. Sem ultralytics (pesado, traz o PyTorch junto): sem modelo
# treinado a rota de verificação por foto já responde 503, o resto do sistema
# funciona normal (ver requirements.txt e docs/pendencias.md).
FROM python:3.13-slim

WORKDIR /app

COPY requirements.txt .
RUN grep -vE '^(#|ultralytics|$)' requirements.txt > requirements.deploy.txt \
    && pip install --no-cache-dir -r requirements.deploy.txt

COPY . .

EXPOSE 8000

CMD ["python", "main.py"]
