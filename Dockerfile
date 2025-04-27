FROM python:3.12-slim

WORKDIR /app

# Install uv
RUN pip install --upgrade pip && pip install uv

# Copy dependency files first for better cache
COPY pyproject.toml .
# If you have poetry.lock, uncomment the next line
# COPY poetry.lock .

# Install main dependencies with uv
RUN uv pip install -r pyproject.toml --system

# Copy the rest of the code
COPY . .

# No CMD needed; docker-compose.yml will set the command 