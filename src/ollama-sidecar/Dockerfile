FROM ollama/ollama:latest

COPY entrypoint.sh /entrypoint.sh
# CRLF で持ち込まれても Linux で exec できるよう CR を除去してから実行権限を付与
RUN sed -i 's/\r$//' /entrypoint.sh && chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
