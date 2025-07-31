# 1. Start from a modern base image with a recent Python version
FROM node:22-bookworm

# 2. Install Python tools and the required 'libmagic1' system library
RUN apt-get update && apt-get install -y python3 python3-pip python3.11-venv libmagic1 && rm -rf /var/lib/apt/lists/*

# 3. Set the main working directory for the project
WORKDIR /app

# 4. Install frontend dependencies
COPY frontend/package*.json ./frontend/
# Update npm to the latest version to avoid installer bugs
RUN npm install -g npm@latest
WORKDIR /app/frontend
RUN npm install

# 5. Install backend dependencies using a virtual environment
WORKDIR /app
COPY backend/requirements.txt ./backend/
WORKDIR /app/backend
# Create a virtual environment
RUN python3 -m venv /opt/venv
# Add the venv's bin directory to the system's PATH
ENV PATH="/opt/venv/bin:$PATH"
# Install packages into the virtual environment
RUN pip install --no-cache-dir -r requirements.txt

# 6. Go back to the project root and copy all the application code
WORKDIR /app
COPY . .