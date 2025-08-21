#!/bin/bash
cd /root/openhermes_backend
source venv/bin/activate
pkill -f main_production
taskset -c 4-7 nice -n -20 python main_production.py
