FROM python:3.10-slim

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    libportaudio2 \
    build-essential \
    alsa-utils \
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
# When running this container, ensure you share the host's sound device, e.g.:
# docker run -it --rm -p 8888:8888 --device /dev/snd <your_image_name>
CMD ["jupyter", "notebook", "--ip", "0.0.0.0", "--port", "8888", "--allow-root", "--no-browser"]
