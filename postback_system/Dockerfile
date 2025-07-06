FROM python:3.11-slim

WORKDIR /app

# Install dependencies
RUN pip install fastapi uvicorn[standard] python-multipart

# Copy test server
COPY test_server.py .

# Expose port
EXPOSE 8080

# Run the application
CMD ["python", "test_server.py"]
