#!/bin/bash

echo "🚀 Starting BioFeed Deployment..."

# 1. Pull latest changes
echo "📥 Pulling changes from Git..."
git pull origin main

# 2. Update Database
echo "🗄️ Migrating Database..."
source venv/bin/activate
python update_db.py

# 3. Restart Service
echo "🔄 Restarting Gunicorn Service..."
sudo systemctl restart biofeed

# 4. Check Status
echo "✅ Checking Service Status..."
sudo systemctl status biofeed --no-pager

echo "🎉 Deployment Complete!"
