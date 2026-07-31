
# Use a more modern and supported base image (Debian Bookworm)
FROM python:3.10-slim-bookworm

# Set environment variables for non-interactive installation
ENV DEBIAN_FRONTEND=noninteractive

# Install Java Development Kit (JDK), wget, and unzip
RUN apt-get update && apt-get install -y --no-install-recommends \
    openjdk-17-jdk \
    wget \
    unzip \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Install apktool
ENV APKTOOL_VERSION=2.9.3
RUN wget https://bitbucket.org/iBotPeaches/apktool/downloads/apktool_${APKTOOL_VERSION}.jar -O /usr/local/bin/apktool.jar \
    && wget https://raw.githubusercontent.com/iBotPeaches/Apktool/master/scripts/linux/apktool -O /usr/local/bin/apktool \
    && chmod +x /usr/local/bin/apktool \
    && chmod +x /usr/local/bin/apktool.jar

# Install uber-apk-signer
ENV UBER_APK_SIGNER_VERSION=1.3.0
RUN wget https://github.com/patrickfav/uber-apk-signer/releases/download/v${UBER_APK_SIGNER_VERSION}/uber-apk-signer-${UBER_APK_SIGNER_VERSION}.jar -O /usr/local/bin/uber-apk-signer.jar

# Set the working directory
WORKDIR /app

# Copy the project files
COPY . /app

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Use shell form for CMD to allow dynamic port expansion from Railway
CMD uvicorn main:app --host 0.0.0.0 --port ${PORT:-8080}
