#!/bin/sh
set -e

# Ollama サーバーを起動
ollama serve &
SERVE_PID=$!

# サーバーの起動を待ってからモデル本体を pull
sleep 5
ollama pull qwen2.5:3b-instruct-q4_K_M

# フォアグラウンドの serve プロセスを待つ（コンテナを終了させない）
wait "$SERVE_PID"
