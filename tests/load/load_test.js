/**
 * K6 load test for HLAV API
 * 
 * Run with:
 *   k6 run tests/load/load_test.js
 * 
 * Or with custom parameters:
 *   k6 run --vus 50 --duration 30s tests/load/load_test.js
 */

import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate } from 'k6/metrics';

// Custom metrics
const errorRate = new Rate('errors');

// Test configuration
export const options = {
  stages: [
    { duration: '30s', target: 20 },  // Ramp up to 20 users
    { duration: '1m', target: 50 },   // Stay at 50 users
    { duration: '30s', target: 100 }, // Spike to 100 users
    { duration: '1m', target: 50 },   // Back to 50 users
    { duration: '30s', target: 0 },   // Ramp down
  ],
  thresholds: {
    'http_req_duration': ['p(95)<1000'], // 95% of requests should be below 1s
    'errors': ['rate<0.1'],              // Error rate should be below 10%
  },
};

const BASE_URL = __ENV.API_BASE_URL || 'http://localhost:8000';

// Sample base64 encoded image (white 224x224 image)
const SAMPLE_IMAGE_B64 = '/9j/4AAQSkZJRgABAQAAAQABAAD/2wBDAAgGBgcGBQgHBwcJCQgKDBQNDAsLDBkSEw8UHRofHh0aHBwgJC4nICIsIxwcKDcpLDAxNDQ0Hyc5PTgyPC4zNDL/wAALCAABAAEBAREA/8QAFQABAQAAAAAAAAAAAAAAAAAAAAv/xAAUEAEAAAAAAAAAAAAAAAAAAAAA/9oACAEBAAE/A0//2Q==';

export default function () {
  // Test 1: Health check
  const healthRes = http.get(`${BASE_URL}/healthz`);
  check(healthRes, {
    'health status is 200': (r) => r.status === 200,
    'health ok is true': (r) => r.json('ok') === true,
  }) || errorRate.add(1);

  sleep(0.5);

  // Test 2: Geo status
  const geoStatusRes = http.get(`${BASE_URL}/geo/status`);
  check(geoStatusRes, {
    'geo status is 200': (r) => r.status === 200,
  }) || errorRate.add(1);

  sleep(0.5);

  // Test 3: Image verification
  const verifyPayload = JSON.stringify({
    image_b64: SAMPLE_IMAGE_B64,
    challenge_word: 'orchid',
  });

  const verifyRes = http.post(`${BASE_URL}/verify`, verifyPayload, {
    headers: { 'Content-Type': 'application/json' },
  });

  check(verifyRes, {
    'verify status is 200': (r) => r.status === 200,
    'verify has response': (r) => r.json('ok') !== undefined,
  }) || errorRate.add(1);

  sleep(1);
}
