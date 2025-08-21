#!/bin/bash
echo "=== Sarah AI Performance Benchmark ==="
echo "Configuration: 4 dedicated cores (4-7)"
echo "======================================="

# Different prompt lengths
prompts=(
    "Hi"
    "What is AI?"
    "Explain quantum computing"
    "Write a detailed explanation of machine learning"
)

tokens=(50 100 150 200)

total_time=0
total_tokens=0

for i in {0..3}; do
    prompt="${prompts[$i]}"
    max_tok="${tokens[$i]}"
    
    echo -e "\nTest $((i+1)): '$prompt' (max $max_tok tokens)"
    
    result=$(curl -s -X POST http://localhost:8000/api/chat \
      -H "Content-Type: application/json" \
      -d "{\"message\": \"$prompt\", \"max_tokens\": $max_tok}")
    
    time=$(echo $result | jq -r '.stats.time')
    tok=$(echo $result | jq -r '.stats.tokens')
    tps=$(echo $result | jq -r '.stats.tokens_per_second')
    
    total_time=$(echo "$total_time + $time" | bc)
    total_tokens=$(echo "$total_tokens + $tok" | bc)
    
    printf "  Result: %3d tokens in %5.2fs = %5.1f tok/s\n" $tok $time $tps
    
    sleep 1
done

avg_tps=$(echo "scale=1; $total_tokens / $total_time" | bc)
echo -e "\n======================================="
echo "Average Performance: $avg_tps tok/s"
echo "Total: $total_tokens tokens in ${total_time}s"
