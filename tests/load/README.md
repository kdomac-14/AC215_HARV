# Load Testing

Load tests for the HARV API using k6.

## Prerequisites

Install k6:
```bash
# macOS
brew install k6

# Linux
sudo apt-key adv --keyserver hkp://keyserver.ubuntu.com:80 --recv-keys C5AD17C747E3415A3642D57D77C6C491D6AC1D69
echo "deb https://dl.k6.io/deb stable main" | sudo tee /etc/apt/sources.list.d/k6.list
sudo apt-get update
sudo apt-get install k6

# Windows
choco install k6
```

## Running Load Tests

### Basic run
```bash
k6 run tests/load/load_test.js
```

### Custom parameters
```bash
# 100 virtual users for 60 seconds
k6 run --vus 100 --duration 60s tests/load/load_test.js

# Custom API URL
k6 run --env API_BASE_URL=http://localhost:8000 tests/load/load_test.js
```

### Generate HTML report
```bash
k6 run tests/load/load_test.js --out json=evidence/load/results.json
```

## Test Scenarios

The load test includes:
1. **Health check** - Verify service availability
2. **Geo status** - Check geolocation endpoint
3. **Image verification** - Test inference endpoint with sample image

## Load Profile

- **Ramp up**: 0 → 20 users (30s)
- **Steady**: 50 users (1 min)
- **Spike**: 100 users (30s)
- **Recovery**: 50 users (1 min)
- **Ramp down**: 50 → 0 users (30s)

## Success Criteria

- 95% of requests complete within 1 second
- Error rate < 10%
- No service crashes under load

## Interpreting Results

Key metrics:
- **http_req_duration**: Response time (p95 should be < 1s)
- **http_req_failed**: Failed requests (should be < 10%)
- **iterations**: Total completed test iterations
- **vus**: Virtual users at any time

Example output:
```
     ✓ health status is 200
     ✓ verify status is 200

     checks.........................: 95.00% ✓ 9500  ✗ 500
     data_received..................: 2.3 MB 38 kB/s
     data_sent......................: 1.5 MB 25 kB/s
     http_req_duration..............: avg=145ms  min=20ms  med=120ms  max=980ms  p(95)=450ms
     http_reqs......................: 5000   83.33/s
     iterations.....................: 1000   16.67/s
```
