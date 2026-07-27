
# Use an official Python runtime as a parent image
FROM python:3.10-slim-buster

# Set environment variables for non-interactive installation
ENV DEBIAN_FRONTEND=noninteractive

# Install Java Development Kit (JDK) for apktool and uber-apk-signer
RUN apt-get update && apt-get install -y --no-install-recommends openjdk-17-jdk \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Install wget and unzip for downloading tools
RUN apt-get update && apt-get install -y --no-install-recommends wget unzip \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Install apktool
# Check for the latest version on https://ibotpeaches.github.io/Apktool/install/
ENV APKTOOL_VERSION=2.9.3
RUN wget https://bitbucket.org/iBotPeaches/apktool/downloads/apktool_${APKTOOL_VERSION}.jar -O /usr/local/bin/apktool.jar \
    && wget https://raw.githubusercontent.com/iBotPeaches/Apktool/master/scripts/linux/apktool -O /usr/local/bin/apktool \
    && chmod +x /usr/local/bin/apktool \
    && chmod +x /usr/local/bin/apktool.jar

# Install uber-apk-signer
# Check for the latest version on https://github.com/patrickfav/uber-apk-signer/releases
ENV UBER_APK_SIGNER_VERSION=1.3.0
RUN wget https://github.com/patrickfav/uber-apk-signer/releases/download/v${UBER_APK_SIGNER_VERSION}/uber-apk-signer-${UBER_APK_SIGNER_VERSION}.jar -O /usr/local/bin/uber-apk-signer.jar

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Expose the port the app runs on
EXPOSE 8000

# Run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
