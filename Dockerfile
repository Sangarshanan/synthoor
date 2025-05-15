FROM python:3.10-slim
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    libportaudio2 \
    build-essential \
    alsa-utils \
    && rm -rf /var/lib/apt/lists/*

# Set the path
ENV PATH="/app/.venv/bin:$PATH"

# Copy necessary files
COPY pyproject.toml uv.lock src /app/

# Set working directory for installation
WORKDIR /app

# Install Python packages using uv
RUN uv sync --locked

# Copy tutorial notebooks
COPY tutorial/ /tutorial/

# Set working directory for running the notebook
WORKDIR /tutorial

# Expose the port Jupyter Notebook will run on
EXPOSE 8888

# Command to start Jupyter Notebook
# When running this container, ensure you share the host's sound device, e.g.:
# docker run -it --rm -p 8888:8888 --device /dev/snd <your_image_name>
CMD ["uv", "run", "jupyter", "notebook", "--ip", "0.0.0.0", "--port", "8888", "--allow-root", "--no-browser"]
