/**
 * Quickstart:
 * 1) cd infra && npm install
 * 2) pulumi stack init <stack-name>   # first time only
 * 3) pulumi config set gcp:project <project-id>
 * 4) pulumi config set gcp:region <region> && pulumi config set gcp:zone <zone>  # e.g. us-central1 / us-central1-a
 * 5) optional: pulumi config set nodeCount 3 && pulumi config set nodeMachineType e2-standard-4
 * 6) pulumi up
 *
 * Exports: cluster name, endpoint, kubeconfig (usable by Kubernetes providers).
 */

import * as pulumi from "@pulumi/pulumi";
import * as gcp from "@pulumi/gcp";
import * as k8s from "@pulumi/kubernetes";

const stackConfig = new pulumi.Config();
const harvConfig = new pulumi.Config("harv");
const gcpConfig = new pulumi.Config("gcp");

const project = gcpConfig.require("project");
const region = gcpConfig.require("region");
const zone = gcpConfig.get("zone") ?? `${region}-a`;

const nodeCount = stackConfig.getNumber("nodeCount") ?? 2;
const nodeMachineType = stackConfig.get("nodeMachineType") ?? "e2-standard-2";

const clusterName = `harv-cluster-${pulumi.getStack()}`;

const cluster = new gcp.container.Cluster("harv-cluster", {
    name: clusterName,
    location: zone,
    initialNodeCount: 1,
    removeDefaultNodePool: true,
    networkingMode: "VPC_NATIVE",
    releaseChannel: { channel: "REGULAR" },
    workloadIdentityConfig: {
        workloadPool: `${project}.svc.id.goog`,
    },
    ipAllocationPolicy: {}, // VPC_NATIVE defaults to IP aliases; empty block satisfies API
    loggingService: "logging.googleapis.com/kubernetes",
    monitoringService: "monitoring.googleapis.com/kubernetes",
});

const nodePool = new gcp.container.NodePool("harv-node-pool", {
    cluster: cluster.name,
    location: zone,
    nodeCount,
    management: { autoRepair: true, autoUpgrade: true },
    nodeConfig: {
        machineType: nodeMachineType,
        oauthScopes: ["https://www.googleapis.com/auth/cloud-platform"],
        workloadMetadataConfig: { mode: "GKE_METADATA" },
        labels: { app: "harv" },
        tags: ["harv", "pulumi"],
    },
}, {
    // Avoid no-op update attempts where GKE rejects empty patch bodies.
    ignoreChanges: ["nodeConfig"],
});

const kubeconfig = pulumi
    .all([cluster.name, cluster.endpoint, cluster.masterAuth])
    .apply(([name, endpoint, masterAuth]) => {
        const context = `${name}`;

        return `apiVersion: v1
clusters:
- cluster:
    certificate-authority-data: ${masterAuth.clusterCaCertificate}
    server: https://${endpoint}
  name: ${name}
contexts:
- context:
    cluster: ${name}
    user: ${name}
  name: ${context}
current-context: ${context}
kind: Config
preferences: {}
users:
- name: ${name}
  user:
    exec:
      apiVersion: client.authentication.k8s.io/v1beta1
      command: gke-gcloud-auth-plugin
      args:
        - --use_application_default_credentials
      interactiveMode: Never
`;
    });

export const gkeClusterName = cluster.name;
export const gkeClusterEndpoint = cluster.endpoint;
export const gkeKubeconfig = kubeconfig;

export const k8sProvider = new k8s.Provider("harv-gke-provider", {
    kubeconfig,
}, { dependsOn: [nodePool] });

// Backend API on GKE
const backendImage = harvConfig.require("backendImage");
const backendReplicas = stackConfig.getNumber("backendReplicas") ?? 2;
const backendEnv = harvConfig.getObject<Record<string, string>>("backendEnv") ?? {};
const backendSecretEnv = harvConfig.getSecretObject<Record<string, string>>("backendSecretEnv");
const backendLabels = { app: "harv-backend" };

const backendSecret = backendSecretEnv
    ? new k8s.core.v1.Secret("harv-backend-secret", {
        metadata: { name: "harv-backend-secret" },
        stringData: backendSecretEnv,
    }, { provider: k8sProvider })
    : undefined;

const harvBackendDeployment = new k8s.apps.v1.Deployment("harv-backend", {
    metadata: { name: "harv-backend", labels: backendLabels },
    spec: {
        replicas: backendReplicas,
        selector: { matchLabels: backendLabels },
        template: {
            metadata: { labels: backendLabels },
            spec: {
                containers: [{
                    name: "harv-backend",
                    image: backendImage,
                    ports: [{ containerPort: 8000 }],
                    env: Object.entries(backendEnv).map(([name, value]) => ({ name, value })),
                    envFrom: backendSecret ? [{ secretRef: { name: backendSecret.metadata.name } }] : undefined,
                }],
            },
        },
    },
}, { provider: k8sProvider, dependsOn: backendSecret ? [backendSecret] : undefined });

const harvBackendService = new k8s.core.v1.Service("harv-backend-svc", {
    metadata: { name: "harv-backend-svc", labels: backendLabels },
    spec: {
        type: "ClusterIP",
        selector: backendLabels,
        ports: [{ name: "http", port: 80, targetPort: 8000 }],
    },
}, { provider: k8sProvider });

const harvBackendLoadBalancer = new k8s.core.v1.Service("harv-backend-lb", {
    metadata: { name: "harv-backend-lb", labels: backendLabels },
    spec: {
        type: "LoadBalancer",
        selector: backendLabels,
        ports: [{ name: "http", port: 80, targetPort: 8000 }],
    },
}, { provider: k8sProvider });

const harvBackendHpa = new k8s.autoscaling.v2.HorizontalPodAutoscaler("harv-backend-hpa", {
    metadata: { name: "harv-backend-hpa" },
    spec: {
        scaleTargetRef: {
            apiVersion: "apps/v1",
            kind: "Deployment",
            name: harvBackendDeployment.metadata.name,
        },
        minReplicas: 2,
        maxReplicas: 5,
        metrics: [{
            type: "Resource",
            resource: {
                name: "cpu",
                target: { type: "Utilization", averageUtilization: 80 },
            },
        }],
    },
}, { provider: k8sProvider });

export const backendExternalUrl = harvBackendLoadBalancer.status.loadBalancer.ingress.apply(ingress => {
    const address = ingress?.[0]?.ip ?? ingress?.[0]?.hostname ?? "";
    return address ? `http://${address}` : "";
});
