#!/bin/bash
while true; do
    clear
    echo "=== CPU Core Usage ==="
    echo "Cores 0-3 (System/Frontend/DB):"
    mpstat -P 0,1,2,3 1 1 | grep Average
    echo ""
    echo "Cores 4-7 (Model):"
    mpstat -P 4,5,6,7 1 1 | grep Average
    sleep 2
done
