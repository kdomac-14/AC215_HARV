#!/bin/bash
set -e

MAX_ATTEMPTS=${MAX_ATTEMPTS:-30}
SLEEP_INTERVAL=${SLEEP_INTERVAL:-2}
API_URL=${API_BASE_URL:-http://localhost:8000}

echo "Waiting for services to be ready..."
echo "API URL: ${API_URL}"
echo "Max attempts: ${MAX_ATTEMPTS}"

attempt=0
while [ $attempt -lt $MAX_ATTEMPTS ]; do
    if curl -s -f "${API_URL}/healthz" > /dev/null 2>&1; then
        echo "✓ Services are ready after $((attempt * SLEEP_INTERVAL)) seconds"
        exit 0
    fi
    
    attempt=$((attempt + 1))
    echo "  Attempt ${attempt}/${MAX_ATTEMPTS}..."
    sleep $SLEEP_INTERVAL
done

echo "✗ Services did not become ready within $((MAX_ATTEMPTS * SLEEP_INTERVAL)) seconds"
exit 1
