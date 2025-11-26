#!/bin/bash
# Make all deployment scripts executable
# Run this once after cloning the repository

chmod +x deploy/deploy.sh
chmod +x deploy/backup-database.sh
chmod +x deploy/setup-server.sh
chmod +x deploy/make-executable.sh

echo "✓ All deployment scripts are now executable"

