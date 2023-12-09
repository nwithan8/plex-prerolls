#!/bin/sh

# Create cron directory
mkdir -p /etc/cron.d

# Read cron schedule from environment variable
CRON_SCHEDULE=${CRON_SCHEDULE:-"0 0 * * *"} # Default to midnight every day if not supplied

# Add "--dry-run" flag if DRY_RUN is set to true
if [ "$DRY_RUN" = "true" ]; then
    DRY_RUN_FLAG="--dry-run"
else
    DRY_RUN_FLAG=""
fi

# DRY_RUN_FLAG="--dry-run"

# Schedule cron job with supplied cron schedule
echo "$CRON_SCHEDULE python3 /run.py -c /config.yaml -l /logs $DRY_RUN_FLAG > /proc/1/fd/1 2>/proc/1/fd/2" > /etc/cron.d/schedule_preroll

# Give execution rights on the cron job
chmod 0644 /etc/cron.d/schedule_preroll

# Apply cron job
crontab /etc/cron.d/schedule_preroll

# Create the log file to be able to run tail
touch /var/log/cron.log

# Run the command on container startup
crond && tail -f /var/log/cron.log
