# Use an official Python runtime as a parent image
FROM python:3.10-slim

# Set the working directory in the container
WORKDIR /app

# Copy the microservice requirements file into the container at /app
COPY microservice/requirements.txt .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the microservice source code and other necessary files into the container at /app
# Adjust the COPY instructions based on your microservice structure
COPY microservice/src/ ./src
COPY ir/ ./ir
# Add other COPY lines if your microservice needs access to other parts of the project

# Make port 80 available to the world outside this container (if applicable)
# EXPOSE 80

# Define environment variable
ENV NAME QuantumMicroservice

# Run the application when the container launches
# Replace main.py with the entry point of your microservice
# CMD ["python", "src/main.py"]
