FROM python:3.12-slim

# Install FFmpeg + ffprobe
RUN apt-get update && \
    apt-get install -y ffmpeg && \
    rm -rf /var/lib/apt/lists/*

# Your app setup
WORKDIR /app
COPY . .
RUN pip install --no-cache-dir -r requirements.txt

# Deno install (repo needs Deno too)
RUN curl -fsSL https://deno.land/install.sh | sh
ENV PATH="/root/.deno/bin:${PATH}"

CMD ["bash", "start"]
