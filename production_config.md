# Sarah AI Production Configuration

## Optimal Settings (Tested)
- Model: OpenHermes 2.5 Mistral 7B Q4_K_M
- Cores: 4-7 (dedicated to model)
- Threads: 4
- Batch Size: 256
- Context: 1024
- Average Speed: 15-17 tok/s

## Performance by Token Count
- Short (25 tokens): ~12 tok/s
- Medium (100 tokens): ~15 tok/s
- Long (200 tokens): ~17 tok/s

## System Configuration
- CPU Governor: Default (ondemand)
- Process Priority: -20 (highest)
- CPU Affinity: taskset -c 4-7

## DO NOT CHANGE
- Don't set performance governor (makes it slower)
- Keep 4 threads (matches 4 cores)
- Keep default CPU scaling

## Launch Command
```bash
cd /root/openhermes_backend
source venv/bin/activate
taskset -c 4-7 nice -n -20 python main_4core_optimized.py &
