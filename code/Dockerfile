# Get Debian
FROM debian:bullseye-slim

# Environment variables
ENV CONDA_DIR=/opt/conda
ENV JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64

# Setup system dependencies
RUN --mount=type=cache,target=/var/cache/apt \
    apt-get update && apt-get install -y \
    wget curl git build-essential libhdf5-dev \
    openjdk-17-jdk procps && \
    rm -rf /var/lib/apt/lists/*

# Set PATH to include Conda and Java
ENV PATH="$CONDA_DIR/bin:$JAVA_HOME/bin:$PATH"

# Install Miniconda
RUN wget -qO /tmp/miniconda.sh https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh && \
    bash /tmp/miniconda.sh -b -p $CONDA_DIR && \
    rm -f /tmp/miniconda.sh

# Init Conda in the shell
RUN echo ". $CONDA_DIR/etc/profile.d/conda.sh" >> ~/.bashrc

# Copy and install environment dependencies
COPY environment.yml /tmp/environment.yml
RUN conda env create -f /tmp/environment.yml && conda clean -afy

# Set working directory
WORKDIR /app

# Create necessary directories
RUN mkdir -p /app/logs /app/ztmp/data

# Copy project files into /app
COPY code /app/code

# Ensure script is executable
RUN chmod +x /app/code/script/run.sh

# Set permissions for directories
RUN chmod 777 /app/logs /app/ztmp/data

# Use Bash shell and run the script
CMD ["/bin/bash", "-c", "/app/code/script/run.sh; tail -f /dev/null"]
