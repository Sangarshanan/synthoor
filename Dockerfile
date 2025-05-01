FROM python:3.10-slim

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    libportaudio2 \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip, setuptools & uv
RUN pip install -U pip setuptools uv

# Copy necessary files
COPY pyproject.toml requirements.txt src /app/

# Set working directory for installation
WORKDIR /app

# Install Python packages using uv
RUN uv pip install --system .

# Copy tutorial notebooks
COPY tutorial/ /tutorial/

# Set working directory for running the notebook
WORKDIR /tutorial

# Expose the port Jupyter Notebook will run on
EXPOSE 8888

# Command to start Jupyter Notebook
CMD ["jupyter", "notebook", "--ip", "0.0.0.0", "--port", "8888", "--allow-root", "--no-browser"]
