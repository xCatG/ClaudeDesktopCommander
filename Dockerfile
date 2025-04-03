# Dockerfile for Python Desktop Commander MCP
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY . .

# Install the package
RUN pip install -e .

# Expose port if needed
# EXPOSE 8080

# Command to run the server
CMD ["python", "-m", "desktop_commander.main"]