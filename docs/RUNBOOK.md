# HARV Production Operations Runbook

> **SRE Runbook** – Operational procedures for HARV in production

---

## Table of Contents

1. [System Overview](#1-system-overview)
2. [Key Commands](#2-key-commands)
3. [Deployment Procedures](#3-deployment-procedures)
4. [Model Management](#4-model-management)
5. [Incident Response](#5-incident-response)
6. [Logs & Monitoring](#6-logs--monitoring)
7. [Post-Incident Actions](#7-post-incident-actions)

---

## 1. System Overview

### Architecture Summary

HARV (Harvard Attendance Recognition and Verification) runs on **Google Kubernetes Engine (GKE)** as a FastAPI backend serving GPS-based attendance verification with ML-powered face recognition fallback. Traffic enters through a **GCP Load Balancer** provisioned by a Kubernetes Service, distributing requests across 2-5 backend pods managed by a **Horizontal Pod Autoscaler (HPA)**. The ML model (MobileNetV3-Small, TorchScript format) is loaded from **Google Cloud Storage** at container startup. Attendance data persists in **Firestore**.

### Production Definition

| Component | Production State |
|-----------|------------------|
| **Compute** | GKE cluster (`harv-cluster-prod`) in `us-central1-a` |
| **Networking** | LoadBalancer Service with external IP |
| **Scaling** | HPA: 2 min, 5 max replicas @ 80% CPU target |
| **Container Registry** | `us-central1-docker.pkg.dev/ac215-475022/harv-backend` |
| **Model Storage** | `gs://ac215-475022-assets/artifacts/model/` |
| **Database** | Firestore (Native mode) |
| **IaC** | Pulumi stack: `prod` |

### Service Endpoints

| Endpoint | Purpose | Expected Response |
|----------|---------|-------------------|
| `GET /health` | Health check | `{"ok": true, "app": "harv"}` |
| `POST /api/checkin/gps` | GPS attendance | `{"status": "present"}` |
| `POST /api/checkin/vision` | Vision fallback | `{"verified": true}` |
| `GET /api/instructor/attendance` | Attendance roster | JSON array |

### Contact & Escalation

| Role | Contact | When to Escalate |
|------|---------|------------------|
| **On-Call Engineer** | Slack: `#harv-oncall` | First responder |
| **Tech Lead** | Email: `harv-leads@` | P1/P2 incidents |
| **Infrastructure** | Slack: `#infra-support` | GKE/GCP issues |

---

## 2. Key Commands

### Quick Reference Card

```bash
# ============================================
# HARV Production Operations - Quick Reference
# ============================================

# --- Cluster Access ---
export KUBECONFIG=~/.kube/harv-prod-config
gcloud container clusters get-credentials harv-cluster-prod \
  --zone us-central1-a --project ac215-475022

# --- Pod Status ---
kubectl get pods -l app=harv-backend
kubectl get pods -l app=harv-backend -o wide  # with node info

# --- Service Status ---
kubectl get svc harv-backend-lb
kubectl get endpoints harv-backend-svc

# --- HPA Status ---
kubectl get hpa harv-backend-hpa
kubectl describe hpa harv-backend-hpa

# --- Logs ---
kubectl logs -l app=harv-backend --tail=100
kubectl logs -l app=harv-backend -f  # follow

# --- Quick Health Check ---
LB_IP=$(kubectl get svc harv-backend-lb -o jsonpath='{.status.loadBalancer.ingress[0].ip}')
curl http://$LB_IP/health
```

### 2.1 Check Pod Status

```bash
# List all backend pods
kubectl get pods -l app=harv-backend

# Example output:
# NAME                            READY   STATUS    RESTARTS   AGE
# harv-backend-6d4f5b7c8d-abc12   1/1     Running   0          2h
# harv-backend-6d4f5b7c8d-def34   1/1     Running   0          2h

# Detailed pod info
kubectl get pods -l app=harv-backend -o wide

# Check pod events (useful for debugging)
kubectl describe pod <pod-name>

# Check all pods across namespaces (if needed)
kubectl get pods --all-namespaces | grep harv
```

### 2.2 Restart Deployment

```bash
# Rolling restart (zero-downtime)
kubectl rollout restart deployment/harv-backend

# Watch rollout progress
kubectl rollout status deployment/harv-backend

# Example output:
# deployment "harv-backend" successfully rolled out

# Force restart specific pod (delete and let deployment recreate)
kubectl delete pod <pod-name>
```

### 2.3 Port-Forward for Debugging

```bash
# Forward local port to pod (bypasses load balancer)
kubectl port-forward deployment/harv-backend 8000:8000

# In another terminal:
curl http://localhost:8000/health

# Forward to specific pod
kubectl port-forward pod/harv-backend-6d4f5b7c8d-abc12 8000:8000

# Forward with verbose output
kubectl port-forward deployment/harv-backend 8000:8000 -v=6
```

### 2.4 Check HPA Scaling Metrics

```bash
# Current HPA status
kubectl get hpa harv-backend-hpa

# Example output:
# NAME               REFERENCE                 TARGETS   MINPODS   MAXPODS   REPLICAS   AGE
# harv-backend-hpa   Deployment/harv-backend   15%/80%   2         5         2          3d

# Detailed HPA info (includes events)
kubectl describe hpa harv-backend-hpa

# Watch HPA in real-time
kubectl get hpa harv-backend-hpa --watch

# Check current CPU usage per pod
kubectl top pods -l app=harv-backend

# Check node resources
kubectl top nodes
```

### 2.5 Describe Failed Pods

```bash
# Get pod status with failure reason
kubectl get pods -l app=harv-backend -o jsonpath='{range .items[*]}{.metadata.name}{"\t"}{.status.phase}{"\t"}{.status.containerStatuses[0].state}{"\n"}{end}'

# Describe pod for detailed events
kubectl describe pod <pod-name>

# Key sections to check:
# - Events (bottom of output)
# - State (under Containers)
# - Last State (for crash info)

# Get pod logs from crashed container
kubectl logs <pod-name> --previous

# Get events sorted by time
kubectl get events --sort-by='.lastTimestamp' | grep harv
```

### 2.6 Service & Networking

```bash
# Get Load Balancer external IP
kubectl get svc harv-backend-lb -o jsonpath='{.status.loadBalancer.ingress[0].ip}'

# Check service endpoints (should list pod IPs)
kubectl get endpoints harv-backend-svc

# Test connectivity from within cluster
kubectl run debug --rm -it --image=curlimages/curl -- curl http://harv-backend-svc/health

# Check service configuration
kubectl describe svc harv-backend-lb
```

---

## 3. Deployment Procedures

### 3.1 Standard Deploy (CI/CD)

The standard deployment flow is triggered by merging to `main`:

```
Push to main → GitHub Actions → Build Docker Image → Push to Artifact Registry → Update Pulumi Config → Deploy to GKE
```

**Monitor CI/CD Pipeline:**
1. Go to: https://github.com/kdomac-14/AC215_HARV/actions
2. Watch the latest workflow run
3. Verify all jobs pass (lint, test, build, deploy)

**Verify Deployment:**
```bash
# Check new pods are running
kubectl get pods -l app=harv-backend

# Verify image version
kubectl get deployment harv-backend -o jsonpath='{.spec.template.spec.containers[0].image}'

# Test health endpoint
LB_IP=$(kubectl get svc harv-backend-lb -o jsonpath='{.status.loadBalancer.ingress[0].ip}')
curl http://$LB_IP/health
```

### 3.2 Manual Deploy Using Pulumi

Use when CI/CD is unavailable or for emergency hotfixes:

```bash
# 1. Build and push new image
cd /path/to/AC215_HARV
IMAGE_TAG=$(git rev-parse --short HEAD)
make build-backend-image IMAGE_TAG=$IMAGE_TAG
make push-backend-image IMAGE_TAG=$IMAGE_TAG

# 2. Update Pulumi config
cd infra
pulumi config set harv:backendImage \
  us-central1-docker.pkg.dev/ac215-475022/harv-backend/backend:$IMAGE_TAG

# 3. Preview changes
pulumi preview

# 4. Deploy (requires confirmation)
pulumi up

# 5. Verify deployment
kubectl rollout status deployment/harv-backend
```

### 3.3 Rolling Back to Previous Image

#### Option A: kubectl (Fastest)

```bash
# View deployment history
kubectl rollout history deployment/harv-backend

# Rollback to previous revision
kubectl rollout undo deployment/harv-backend

# Rollback to specific revision
kubectl rollout undo deployment/harv-backend --to-revision=2

# Verify rollback
kubectl rollout status deployment/harv-backend
kubectl get deployment harv-backend -o jsonpath='{.spec.template.spec.containers[0].image}'
```

#### Option B: Pulumi Stack History

```bash
cd infra

# View stack history
pulumi stack history

# Example output:
# VERSION  DATE                 DESCRIPTION
# 5        2024-01-15 10:30:00  Update backend image to abc123
# 4        2024-01-14 15:00:00  Update backend image to def456
# 3        2024-01-13 09:00:00  Initial deployment

# Rollback by setting previous image
pulumi config set harv:backendImage \
  us-central1-docker.pkg.dev/ac215-475022/harv-backend/backend:<previous-tag>
pulumi up
```

#### Option C: Direct Image Update

```bash
# Set specific image version directly
kubectl set image deployment/harv-backend \
  harv-backend=us-central1-docker.pkg.dev/ac215-475022/harv-backend/backend:<tag>

# Watch rollout
kubectl rollout status deployment/harv-backend
```

---

## 4. Model Management

### 4.1 View Current Production Model Version

```bash
# Check model metadata in GCS
gsutil cat gs://ac215-475022-assets/artifacts/model/metadata.json | jq .

# Example output:
# {
#   "model_name": "mobilenet_v3_small",
#   "version": "v1.2.0",
#   "accuracy": 0.92,
#   "created_at": "2024-01-15T10:00:00Z",
#   "commit_sha": "abc1234"
# }

# Check model file timestamp
gsutil ls -l gs://ac215-475022-assets/artifacts/model/

# Verify model loaded in running pods
kubectl exec -it deployment/harv-backend -- cat /app/artifacts/model/metadata.json
```

### 4.2 Manually Promote a Model

```bash
# 1. Verify new model exists in staging location
gsutil ls gs://ac215-475022-assets/artifacts/staging/model/

# 2. Backup current production model
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
gsutil -m cp -r gs://ac215-475022-assets/artifacts/model/ \
  gs://ac215-475022-assets/artifacts/model_backup_$TIMESTAMP/

# 3. Promote staging model to production
gsutil -m cp -r gs://ac215-475022-assets/artifacts/staging/model/* \
  gs://ac215-475022-assets/artifacts/model/

# 4. Restart pods to load new model
kubectl rollout restart deployment/harv-backend

# 5. Verify new model is loaded
kubectl logs -l app=harv-backend | grep "Model loaded"

# 6. Test inference
LB_IP=$(kubectl get svc harv-backend-lb -o jsonpath='{.status.loadBalancer.ingress[0].ip}')
curl -X POST http://$LB_IP/api/checkin/vision \
  -H "Content-Type: application/json" \
  -d '{"image_b64": "<base64-test-image>", "student_id": "test"}'
```

### 4.3 Re-run Training Pipeline

```bash
# Option A: Run via Docker Compose (local)
cd /path/to/AC215_HARV
make all  # Runs: ingest → preprocess → train → evaluate → export

# Option B: Run individual stages
docker compose run --rm ingestion
docker compose run --rm preprocess
docker compose run --rm train
docker compose run --rm evaluate
docker compose run --rm export

# Option C: Run via DVC (if configured)
dvc repro

# After training, upload new model to staging
gsutil -m cp -r ./artifacts/model/* \
  gs://ac215-475022-assets/artifacts/staging/model/

# Review metrics before promotion
cat ./artifacts/metrics.json | jq .
```

### 4.4 Model Rollback

```bash
# List available backups
gsutil ls gs://ac215-475022-assets/artifacts/ | grep model_backup

# Restore specific backup
gsutil -m cp -r gs://ac215-475022-assets/artifacts/model_backup_20240115_100000/* \
  gs://ac215-475022-assets/artifacts/model/

# Restart pods
kubectl rollout restart deployment/harv-backend
```

---

## 5. Incident Response

### INC-001: Backend Returning 5xx Errors

**Severity**: P1 (if >1% of requests affected)

**Symptoms:**
- Users report "Server Error" messages
- Monitoring shows elevated 5xx rate
- Health check returns non-200

**Diagnosis:**

```bash
# 1. Check pod status
kubectl get pods -l app=harv-backend
# Look for: CrashLoopBackOff, Error, or low READY count

# 2. Check recent logs for errors
kubectl logs -l app=harv-backend --tail=200 | grep -i error

# 3. Check if pods are OOMKilled
kubectl describe pods -l app=harv-backend | grep -A5 "Last State"

# 4. Check resource usage
kubectl top pods -l app=harv-backend

# 5. Test health endpoint directly
kubectl port-forward deployment/harv-backend 8000:8000 &
curl http://localhost:8000/health
```

**Resolution:**

```bash
# If pods are crashing:
kubectl rollout restart deployment/harv-backend

# If OOMKilled, increase memory limits:
# Edit infra/index.ts and redeploy, or:
kubectl patch deployment harv-backend --type='json' -p='[
  {"op": "replace", "path": "/spec/template/spec/containers/0/resources/limits/memory", "value": "1Gi"}
]'

# If model loading fails, check GCS permissions:
gsutil ls gs://ac215-475022-assets/artifacts/model/

# Rollback if recent deployment caused issue:
kubectl rollout undo deployment/harv-backend
```

---

### INC-002: ML Model Failing to Load

**Severity**: P1 (service degraded)

**Symptoms:**
- Health check shows `"model": null`
- Vision fallback requests fail
- Logs show "Model not found" or "TorchScript load error"

**Diagnosis:**

```bash
# 1. Check pod logs for model loading errors
kubectl logs -l app=harv-backend | grep -i "model\|torch\|load"

# 2. Verify model exists in GCS
gsutil ls -l gs://ac215-475022-assets/artifacts/model/

# 3. Check model file is valid
gsutil cat gs://ac215-475022-assets/artifacts/model/metadata.json

# 4. Test model download from pod
kubectl exec -it deployment/harv-backend -- ls -la /app/artifacts/model/

# 5. Check service account permissions
gcloud projects get-iam-policy ac215-475022 --flatten="bindings[].members" \
  --filter="bindings.members:harv-service" --format="table(bindings.role)"
```

**Resolution:**

```bash
# If model file is missing or corrupted:
# Re-upload from local artifacts
gsutil -m cp -r ./artifacts/model/* gs://ac215-475022-assets/artifacts/model/

# If permissions issue:
gcloud projects add-iam-policy-binding ac215-475022 \
  --member="serviceAccount:harv-service@ac215-475022.iam.gserviceaccount.com" \
  --role="roles/storage.objectViewer"

# Restart pods to retry model load
kubectl rollout restart deployment/harv-backend

# If still failing, restore from backup
gsutil -m cp -r gs://ac215-475022-assets/artifacts/model_backup_<latest>/* \
  gs://ac215-475022-assets/artifacts/model/
kubectl rollout restart deployment/harv-backend
```

---

### INC-003: Service Unreachable (LB Down / DNS)

**Severity**: P1 (complete outage)

**Symptoms:**
- All requests timeout
- Cannot reach Load Balancer IP
- Mobile app shows "Connection Error"

**Diagnosis:**

```bash
# 1. Check Load Balancer status
kubectl get svc harv-backend-lb

# Look for EXTERNAL-IP: should have IP, not <pending>

# 2. Check LB health
kubectl describe svc harv-backend-lb

# 3. Check endpoints (should list pod IPs)
kubectl get endpoints harv-backend-svc
# If empty, pods are not ready

# 4. Check pods are running and ready
kubectl get pods -l app=harv-backend

# 5. Test from within cluster
kubectl run debug --rm -it --image=curlimages/curl -- \
  curl http://harv-backend-svc/health

# 6. Check GCP Load Balancer in console
# https://console.cloud.google.com/net-services/loadbalancing/list
```

**Resolution:**

```bash
# If EXTERNAL-IP is <pending>:
# Wait up to 5 minutes for IP provisioning
# If still pending, check GCP quotas

# If endpoints are empty:
# Check pod readiness probes
kubectl describe deployment harv-backend | grep -A10 "Readiness"

# Restart deployment
kubectl rollout restart deployment/harv-backend

# If LB is misconfigured, recreate service:
kubectl delete svc harv-backend-lb
cd infra && pulumi up  # Recreates service

# For DNS issues (if using custom domain):
# Check A record points to LB IP
dig harv-api.your-domain.com
```

---

### INC-004: HPA Stuck at Low or High Replicas

**Severity**: P2 (performance degradation or cost)

**Symptoms:**
- HPA shows `<unknown>/80%` for targets
- Replicas stuck at min despite high load
- Replicas stuck at max despite low load

**Diagnosis:**

```bash
# 1. Check HPA status
kubectl get hpa harv-backend-hpa
kubectl describe hpa harv-backend-hpa

# Look for:
# - "unable to get metrics" errors
# - Target shows <unknown>

# 2. Check metrics-server is running
kubectl get pods -n kube-system | grep metrics-server

# 3. Check resource requests are set
kubectl get deployment harv-backend -o yaml | grep -A10 resources

# 4. Check current pod CPU usage
kubectl top pods -l app=harv-backend

# 5. Check HPA events
kubectl get events --field-selector involvedObject.name=harv-backend-hpa
```

**Resolution:**

```bash
# If metrics-server is missing or failing:
# GKE should auto-install; if not:
kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml

# If resource requests not set:
kubectl patch deployment harv-backend --type='json' -p='[
  {"op": "add", "path": "/spec/template/spec/containers/0/resources/requests", 
   "value": {"cpu": "100m", "memory": "256Mi"}}
]'

# If stuck at max, check for:
# - Memory leaks (check pod memory over time)
# - Slow responses causing request queuing
kubectl top pods -l app=harv-backend --containers

# Force scale manually (temporary):
kubectl scale deployment harv-backend --replicas=3

# Reset HPA:
kubectl delete hpa harv-backend-hpa
cd infra && pulumi up  # Recreates HPA
```

---

## 6. Logs & Monitoring

### 6.1 kubectl Logs

```bash
# === Basic Log Commands ===

# Tail logs from all backend pods
kubectl logs -l app=harv-backend --tail=100

# Follow logs in real-time
kubectl logs -l app=harv-backend -f

# Logs from specific pod
kubectl logs harv-backend-6d4f5b7c8d-abc12

# Logs from previous container (after crash)
kubectl logs harv-backend-6d4f5b7c8d-abc12 --previous

# Logs with timestamps
kubectl logs -l app=harv-backend --timestamps

# Logs from last hour
kubectl logs -l app=harv-backend --since=1h

# === Filtering Logs ===

# Search for errors
kubectl logs -l app=harv-backend | grep -i error

# Search for specific request
kubectl logs -l app=harv-backend | grep "student_id.*test123"

# Count error occurrences
kubectl logs -l app=harv-backend | grep -c "ERROR"

# === Multi-container ===

# If pods have multiple containers
kubectl logs <pod-name> -c harv-backend
```

### 6.2 GCP Cloud Logging

Access via: https://console.cloud.google.com/logs/query?project=ac215-475022

**Sample Queries:**

```
# All backend logs
resource.type="k8s_container"
resource.labels.cluster_name="harv-cluster-prod"
resource.labels.container_name="harv-backend"

# Errors only
resource.type="k8s_container"
resource.labels.container_name="harv-backend"
severity>=ERROR

# Specific time range with errors
resource.type="k8s_container"
resource.labels.container_name="harv-backend"
severity>=ERROR
timestamp>="2024-01-15T10:00:00Z"
timestamp<="2024-01-15T11:00:00Z"

# Request latency (if logged)
resource.type="k8s_container"
resource.labels.container_name="harv-backend"
jsonPayload.latency_ms>1000

# 5xx responses
resource.type="k8s_container"
resource.labels.container_name="harv-backend"
jsonPayload.status_code>=500

# Model loading events
resource.type="k8s_container"
resource.labels.container_name="harv-backend"
textPayload=~"model|Model"
```

**Create Log-Based Alert:**
1. Run query in Logs Explorer
2. Click "Create Alert"
3. Set conditions (e.g., >10 errors in 5 minutes)
4. Configure notification channel

### 6.3 Monitoring Dashboards

**GKE Dashboard:**
https://console.cloud.google.com/kubernetes/workload?project=ac215-475022

**Key Metrics to Monitor:**

| Metric | Location | Alert Threshold |
|--------|----------|-----------------|
| Pod CPU | GKE Workloads | >80% sustained |
| Pod Memory | GKE Workloads | >85% |
| Request Latency | Cloud Monitoring | p99 >2s |
| Error Rate | Cloud Logging | >1% of requests |
| Pod Restarts | GKE Workloads | >3 in 10 minutes |

### 6.4 Quick Monitoring Commands

```bash
# Real-time resource usage
watch -n 5 'kubectl top pods -l app=harv-backend'

# Pod restart count
kubectl get pods -l app=harv-backend -o jsonpath='{range .items[*]}{.metadata.name}{"\t"}{.status.containerStatuses[0].restartCount}{"\n"}{end}'

# Recent events
kubectl get events --sort-by='.lastTimestamp' | tail -20

# HPA current state
watch -n 10 'kubectl get hpa harv-backend-hpa'
```

---

## 7. Post-Incident Actions

### 7.1 Generate Incident Report

Create a report using this template:

```markdown
# Incident Report: [INC-XXX] [Brief Title]

## Summary
- **Date/Time**: YYYY-MM-DD HH:MM - HH:MM (duration)
- **Severity**: P1/P2/P3
- **Impact**: [e.g., "50% of GPS check-ins failed for 15 minutes"]
- **Root Cause**: [1-2 sentence summary]

## Timeline (UTC)
| Time | Event |
|------|-------|
| 10:00 | Alert fired: 5xx rate >1% |
| 10:05 | On-call acknowledged |
| 10:10 | Root cause identified: OOMKilled pods |
| 10:15 | Mitigation: Increased memory limits |
| 10:20 | Service restored |

## Root Cause Analysis
[Detailed explanation of what went wrong]

## Resolution
[What was done to fix it]

## Action Items
| Action | Owner | Due Date | Status |
|--------|-------|----------|--------|
| Increase default memory limits | @engineer | 2024-01-20 | TODO |
| Add memory usage alert | @sre | 2024-01-18 | TODO |

## Lessons Learned
- [What we learned]
- [What we'll do differently]
```

### 7.2 Information to Collect

**During Incident:**

```bash
# Save pod state
kubectl get pods -l app=harv-backend -o yaml > incident_pods_$(date +%s).yaml

# Save events
kubectl get events --sort-by='.lastTimestamp' > incident_events_$(date +%s).txt

# Save logs
kubectl logs -l app=harv-backend --since=1h > incident_logs_$(date +%s).txt

# Save HPA state
kubectl describe hpa harv-backend-hpa > incident_hpa_$(date +%s).txt

# Save service state
kubectl get svc,endpoints -o yaml > incident_network_$(date +%s).yaml
```

**After Incident:**

```bash
# Export Cloud Logging data
# Go to Logs Explorer → Run query → Download logs (JSON)

# Get deployment history
kubectl rollout history deployment/harv-backend

# Get Pulumi stack history
cd infra && pulumi stack history > pulumi_history.txt

# Screenshot GKE monitoring graphs for the incident window
```

### 7.3 Post-Incident Checklist

- [ ] Incident report drafted
- [ ] Timeline verified with logs
- [ ] Root cause confirmed
- [ ] Customer communication sent (if applicable)
- [ ] Action items created in issue tracker
- [ ] Runbook updated if procedure was missing
- [ ] Alert thresholds reviewed
- [ ] Post-mortem meeting scheduled (for P1/P2)

---

## Appendix: Command Cheatsheet

```bash
# ===== CLUSTER ACCESS =====
gcloud container clusters get-credentials harv-cluster-prod --zone us-central1-a --project ac215-475022

# ===== STATUS =====
kubectl get pods -l app=harv-backend              # Pod status
kubectl get svc harv-backend-lb                   # Load Balancer IP
kubectl get hpa harv-backend-hpa                  # Autoscaler status
kubectl top pods -l app=harv-backend              # Resource usage

# ===== LOGS =====
kubectl logs -l app=harv-backend --tail=100       # Recent logs
kubectl logs -l app=harv-backend -f               # Follow logs
kubectl logs <pod> --previous                     # Crashed container

# ===== DEBUGGING =====
kubectl describe pod <pod-name>                   # Pod details
kubectl exec -it <pod> -- /bin/sh                 # Shell into pod
kubectl port-forward deployment/harv-backend 8000:8000  # Local access

# ===== DEPLOYMENT =====
kubectl rollout restart deployment/harv-backend   # Restart pods
kubectl rollout undo deployment/harv-backend      # Rollback
kubectl rollout status deployment/harv-backend    # Watch rollout

# ===== SCALING =====
kubectl scale deployment harv-backend --replicas=3  # Manual scale

# ===== MODEL =====
gsutil ls gs://ac215-475022-assets/artifacts/model/  # Check model
gsutil cat gs://ac215-475022-assets/artifacts/model/metadata.json  # Model version
```

---

## Document Information

| Field | Value |
|-------|-------|
| **Version** | 1.0 |
| **Last Updated** | 2024-12-05 |
| **Owner** | HARV SRE Team |
| **Review Cycle** | Quarterly |

---

*For local development setup, see [MOBILE_APP.md](MOBILE_APP.md) and the main [README.md](../README.md).*
