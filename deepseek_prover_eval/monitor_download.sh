#!/bin/bash
# Monitor model download progress

echo "Monitoring HuggingFace model download..."
echo "Press Ctrl+C to stop monitoring"
echo ""

MODEL_CACHE="$HOME/.cache/huggingface/hub/models--deepseek-ai--DeepSeek-Prover-V2-7B"

while true; do
    if [ -d "$MODEL_CACHE" ]; then
        SIZE=$(du -sh "$MODEL_CACHE" 2>/dev/null | awk '{print $1}')
        COUNT=$(find "$MODEL_CACHE" -type f 2>/dev/null | wc -l)
        echo "[$(date +%H:%M:%S)] Cache size: $SIZE | Files: $COUNT"
    else
        echo "[$(date +%H:%M:%S)] Model cache not found yet (download may not have started)"
    fi
    sleep 5
done

