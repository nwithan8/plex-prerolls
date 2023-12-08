FROM python:3.11-alpine3.18
WORKDIR /

# Install Python and other utilities
RUN apk add --no-cache --update alpine-sdk git wget python3 python3-dev ca-certificates musl-dev libc-dev gcc bash nano linux-headers && \
    python3 -m ensurepip && \
    pip3 install --no-cache-dir --upgrade pip setuptools

# Copy requirements.txt from build machine to WORKDIR (/app) folder (important we do this BEFORE copying the rest of the files to avoid re-running pip install on every code change)
COPY requirements.txt requirements.txt

# Install Python requirements
RUN pip3 install --no-cache-dir -r requirements.txt

# Make Docker /config volume for optional config file
VOLUME /config

# Copy logging.conf file from build machine to Docker /config folder
COPY logging.conf /config/

# Copy example config file from build machine to Docker /config folder
# Also copies any existing config.ini file from build machine to Docker /config folder, (will cause the bot to use the existing config file if it exists)
COPY config.ini* /config/

# Copy example schedule file from build machine to Docker /config folder
# Also copies any existing schedules.yaml file from build machine to Docker /config folder, (will cause the bot to use the existing schedule file if it exists)
COPY schedules.yaml* /config/

# Make Docker /logs volume for log file
VOLUME /logs

# Copy source code from build machine to WORKDIR (/app) folder
COPY . .

# Delete unnecessary files in WORKDIR (/app) folder (not caught by .dockerignore)
RUN echo "**** removing unneeded files ****"
RUN rm -rf /requirements.txt

# Run entrypoint.sh script
ENTRYPOINT ["sh", "/entrypoint.sh"]
