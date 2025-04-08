FROM quantum-cli-sdk/microservice-base:latest

WORKDIR /app

COPY . .

EXPOSE ${port}

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "${port}"]
