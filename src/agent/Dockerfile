# src/agent/Dockerfile — エージェント本体のコンテナ（App Service にデプロイ）
# このフォルダ一式（app.py / llm.py / observability_setup.py / start_server.py）をそのまま build する。
FROM python:3.11-slim

WORKDIR /app

# 依存パッケージ
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# アプリ一式（app.py / llm.py / observability_setup.py / start_server.py 等）
COPY . .

# Bot Framework 慣例のポート
ENV PORT=3978
EXPOSE 3978

# 起動（start_server.py を起点にする）
CMD ["python", "start_server.py"]
