FROM quantum-cli-sdk/microservice-base:latest
WORKDIR /app
COPY my-cli-test-app/services/generated/microservice/app.py .
COPY my-cli-test-app/services/generated/microservice/requirements.txt .
COPY my-cli-test-app/services/generated/microservice/circuits ./circuits
COPY my-cli-test-app/services/generated/microservice/quantum_manifest.json .
RUN pip install --no-cache-dir -v -r requirements.txt
EXPOSE 8000
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
