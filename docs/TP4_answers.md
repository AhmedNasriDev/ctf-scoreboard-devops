## Exercise 1 — System Pods

1. kube-apiserver:
   It exposes the Kubernetes API and handles communication with the cluster. Without it, users and cluster components cannot interact with the Kubernetes API.

2. etcd:
   It stores the cluster's state and configuration. Without it, Kubernetes cannot reliably store or retrieve cluster data.

3. kube-scheduler:
   It assigns newly created Pods to suitable Nodes. Without it, unscheduled Pods would remain pending.

## Exercise 2 — Service Selectors and EndpointSlices

The Service uses a label selector to discover matching Pods.

When the Service selector was temporarily changed from `app: scoreboard` to `app: scoreboard-v2`, the EndpointSlice showed no endpoints because no Pod matched the new selector.

After restoring the selector to `app: scoreboard`, the EndpointSlice showed the application Pod endpoint at port 8000.

This demonstrates that Kubernetes Services depend on label selectors to route traffic to the correct Pods.

## Exercise 3 — Health Probes

Initially, the new Pod remained in the `Running` state but was not Ready (`0/1`) because the database was unreachable. Its readiness probe failed with HTTP 503, while its liveness probe using `/healthz` remained successful.

After changing the liveness probe path to `/readyz`, the Pod started restarting repeatedly because the database failure caused the liveness probe to fail as well.

This demonstrates the difference between the two probes:

- **Readiness probe:** Determines whether a Pod is ready to receive traffic.
- **Liveness probe:** Determines whether a container should be restarted.

The liveness probe should check application health independently of external database availability to avoid unnecessary restart loops.

## Exercise 4 — Deployment Rollback

The smoke test passed during the failed release because Kubernetes kept the previous healthy Pod running while the new Pod failed to pull the image and entered the `ErrImagePull` state.

The Deployment used a rolling update strategy, preserving the old working version while the new version was unavailable.

The `kubectl rollout undo deployment/scoreboard` command restored the previous working Deployment revision. Kubernetes recorded the rollback as a new revision rather than deleting the previous rollout history.

After the rollback:
- The original image tag was restored.
- The Pod returned to `1/1 Running`.
- The rollout completed successfully.
- All 12 smoke tests passed.

The local `deployment.yaml` still contained the original image because `kubectl set image` changed the live cluster configuration, not the local manifest file.

## Exercise 5 — Configuration Drift

The following direct changes were made to the live Kubernetes cluster:

1. Changing the `DATABASE_URL` environment variable using `kubectl set env`.
2. Changing the liveness probe using `kubectl patch`.
3. Changing the container image using `kubectl set image`.
4. Scaling the Deployment using `kubectl scale`.

These changes affected the live cluster but were not automatically recorded in the local YAML manifests or GitHub repository.

A colleague who only has access to the GitHub repository cannot see these temporary cluster changes.

Declarative configuration management using YAML manifests and version control (Git) solves this problem by keeping the desired configuration documented and reproducible.

The `kubectl diff` command detects differences between the live cluster and the local manifests, while `kubectl apply -f k8s/` reconciles the cluster with the declared configuration.

After applying the manifests, `kubectl diff -f k8s/` produced no output, confirming that there were no remaining differences.
