FROM quantum-cli-sdk/microservice-base:latest
WORKDIR /app
COPY . .
COPY circuits/ ./circuits/
COPY quantum_manifest.json ./
RUN pip install --no-cache-dir -r requirements.txt
EXPOSE 8000
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
