#!bin/bash

# This crontab utility runs the monthly python rotation analysis script.
cd /data/project_repos/investment-tools
source activate invest

# Run script
python  monthly_rotation_report.py

exit 0

