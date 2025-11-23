#!/bin/bash
set -e

APP_DIR="/home/ec2-user/biofeed"
BACKUP_DIR="/home/ec2-user/biofeed_backup_$(date +%s)"
REPO_URL="https://github.com/DanielMelloo/DANA-BioFeed.git"

echo "Backing up current deployment..."
mv $APP_DIR $BACKUP_DIR

echo "Cloning repository..."
git clone $REPO_URL $APP_DIR

echo "Restoring Virtual Environment..."
mv $BACKUP_DIR/venv $APP_DIR/venv

echo "Restoring Database..."
mkdir -p $APP_DIR/instance
if [ -f "$BACKUP_DIR/instance/feeders_v7.db" ]; then
    cp $BACKUP_DIR/instance/feeders_v7.db $APP_DIR/instance/
    echo "Database restored."
else
    echo "No database found to restore."
fi

echo "Restoring Config (if needed)..."
# cp $BACKUP_DIR/config.py $APP_DIR/config.py # Config is in repo for now

echo "Fixing permissions..."
chown -R ec2-user:ec2-user $APP_DIR
chmod +x $APP_DIR/deploy.sh

echo "Migration Complete!"
