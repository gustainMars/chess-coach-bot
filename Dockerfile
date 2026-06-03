FROM python:3.13-slim

RUN apt-get update && \
    apt-get install -y --no-install-recommends libcairo2 stockfish && \
    rm -rf /var/lib/apt/lists/*

ENV STOCKFISH_PATH=/usr/games/stockfish

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8080
CMD ["python3", "main.py"]
