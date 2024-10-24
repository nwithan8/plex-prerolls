# Node.js 18.19 and Python 3.11.x pre-installed on Alpine Linux 3.19
FROM nwithan8/python-3.x-node-18.19.0-alpine3.19:latest
WORKDIR /

# Copy requirements.txt from build machine to WORKDIR (/app) folder (important we do this BEFORE copying the rest of the files to avoid re-running pip install on every code change)
COPY requirements.txt requirements.txt

# Python virtual environment already exists in base image as /app/venv

# Install Python requirements
# Ref: https://github.com/python-pillow/Pillow/issues/1763
RUN LIBRARY_PATH=/lib:/usr/lib /bin/sh -c "/app/venv/bin/pip install --no-cache-dir setuptools_rust" # https://github.com/docker/compose/issues/8105#issuecomment-775931324
RUN LIBRARY_PATH=/lib:/usr/lib /bin/sh -c "/app/venv/bin/pip install --no-cache-dir -r requirements.txt"

# Make Docker /config volume for optional config file
VOLUME /config

# Copy config file from build machine to Docker /config folder
COPY config.yaml* /config/

# Make Docker /logs volume for log file
VOLUME /logs

# Make Docker /render volume for rendered files
VOLUME /renders

# Make Docker /auto-rolls volume for completed auto-rolls files
VOLUME /auto_rolls

# Copy source code from build machine to WORKDIR (/app) folder
COPY . .

# Delete unnecessary files in WORKDIR (/app) folder (not caught by .dockerignore)
RUN echo "**** removing unneeded files ****"
# Remove all files except .py files and entrypoint.sh (keep all directories)
# RUN find / -type f -maxdepth 1 ! -name '*.py' ! -name 'entrypoint.sh' -delete

# Run entrypoint.sh script
ENTRYPOINT ["sh", "/entrypoint.sh"]
