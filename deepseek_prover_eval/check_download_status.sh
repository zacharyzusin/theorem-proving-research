#!/bin/bash
# Quick status check for model download

echo "=== Download Status Check ==="
echo ""

# Check if download process is running
PID=$(pgrep -f "download_model.py" | head -1)
if [ -n "$PID" ]; then
    echo "✓ Download process is RUNNING (PID: $PID)"
    RUNTIME=$(ps -p $PID -o etime= 2>/dev/null | xargs)
    CPU_MEM=$(ps -p $PID -o pcpu=,pmem= 2>/dev/null)
    if [ -n "$RUNTIME" ]; then
        echo "  Runtime: $RUNTIME"
    fi
    if [ -n "$CPU_MEM" ]; then
        echo "$CPU_MEM" | awk '{printf "  CPU: %s%%, Memory: %s%%\n", $1, $2}'
    fi
else
    echo "✗ Download process NOT running"
    echo "  (Either finished, not started, or crashed)"
fi

echo ""
echo "=== Cache Status ==="

# Check cache directory
CACHE_DIR=$(find ~/.cache/huggingface/hub -name "*deepseek*" -type d 2>/dev/null | head -1)
if [ -n "$CACHE_DIR" ]; then
    SIZE=$(du -sh "$CACHE_DIR" 2>/dev/null | awk '{print $1}')
    COUNT=$(find "$CACHE_DIR" -type f 2>/dev/null | wc -l)
    echo "✓ Model cache found: $CACHE_DIR"
    echo "  Size: $SIZE"
    echo "  Files: $COUNT"
    
    # Estimate progress (model is ~14GB, but compressed download might be different)
    SIZE_BYTES=$(du -sb "$CACHE_DIR" 2>/dev/null | awk '{print $1}')
    SIZE_GB=$(echo "scale=2; $SIZE_BYTES / 1073741824" | bc 2>/dev/null || echo "0")
    if [ -n "$SIZE_GB" ] && [ "$SIZE_GB" != "0" ]; then
        echo "  Estimated: ${SIZE_GB} GB"
    fi
else
    echo "✗ Model cache not found yet"
    echo "  (Download may be in early stages - tokenizer download)"
fi

echo ""
echo "=== Recent Activity ==="
if [ -n "$PID" ]; then
    echo "Process is active. Download in progress..."
    echo "Run this script again in a few minutes to see progress."
else
    # Check if download completed
    if [ -n "$CACHE_DIR" ] && [ -n "$SIZE" ]; then
        if [ "$COUNT" -gt 100 ]; then
            echo "✓ Download appears to be COMPLETE!"
            echo "  Cache has $COUNT files"
        else
            echo "⚠ Download may be incomplete or still in progress"
        fi
    fi
fi

