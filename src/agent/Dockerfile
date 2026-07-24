# src/agent/Dockerfile — エージェント本体のコンテナ（App Service にデプロイ）
# ※ Skills（make-a365-agent）が生成した start_server.py 等をプロジェクト直下に置いてから build する。
#   このフォルダの app.py / llm.py / obo.py / observability_setup.py も同じ場所に集約する。
FROM python:3.11-slim

WORKDIR /app

# 依存パッケージ（生成された requirements があればそれを優先）
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# アプリ一式（app.py / llm.py / obo.py / observability_setup.py / start_server.py 等）
COPY . .

# Bot Framework 慣例のポート
ENV PORT=3978
EXPOSE 3978

# 起動（Skills 生成の start_server.py を起点にする）
CMD ["python", "start_server.py"]
