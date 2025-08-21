#!/bin/bash
while true; do
    # Get current CPU usage
    cpu=$(top -b -n1 | grep "Cpu(s)" | awk '{print $2}')
    mem=$(free -m | awk 'NR==2{printf "%.1f", $3*100/$2}')
    cs=$(vmstat 1 2 | tail -1 | awk '{print $12}')
    
    echo "$(date +%H:%M:%S) - CPU: $cpu% | MEM: $mem% | CS: $cs"
    sleep 1
done
