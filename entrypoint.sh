#!/bin/sh

# Create cron directory
mkdir -p /etc/cron.d

# Read cron schedule from environment variable
CRON_SCHEDULE=${CRON_SCHEDULE:-"0 0 * * *"} # Default to midnight every day if not supplied

echo "Cron schedule: $CRON_SCHEDULE"

# Add "--dry-run" flag if DRY_RUN is set to true
if [ "$DRY_RUN" = "true" ]; then
    DRY_RUN_FLAG="--dry-run"
else
    DRY_RUN_FLAG=""
fi

echo "Dry run flag: $DRY_RUN_FLAG"

# Run script
echo "Running script"
python3 /run.py -c /config/config.yaml -l /logs -s "$CRON_SCHEDULE" $DRY_RUN_FLAG
