#!/bin/bash

# Exit on error
set -e

APP_DIR="/home/ec2-user/biofeed"
USER="ec2-user"

echo "Creating application directory..."
mkdir -p $APP_DIR
cd $APP_DIR

echo "Setting up Virtual Environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi

echo "Installing dependencies..."
./venv/bin/pip install -r requirements.txt
./venv/bin/pip install gunicorn

echo "Configuring Nginx..."
sudo cp biofeed.conf /etc/nginx/conf.d/biofeed.conf

sudo nginx -t
sudo systemctl restart nginx

echo "Configuring Systemd..."
sudo cp biofeed.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable biofeed
sudo systemctl restart biofeed

echo "Fixing permissions..."
sudo chown -R $USER:$USER $APP_DIR

echo "Deployment Complete! App should be running on port 80 (proxied to 8001)."
