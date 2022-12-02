# Cheat Sheet for Ray

## Check that the KubeRay operator is runnning

```
kubectl -n ray-system get pod --selector=app.kubernetes.io/component=kuberay-operator
```

## List Ray Clusters

```
kubectl get raycluster
```

## Check pods status of RayCluster autoscaler

```
kubectl get pods --selector=ray.io/cluster=raycluster-autoscaler
```

## Get Head nodes of clusters

```
kubectl get pods --selector=ray.io/cluster=raycluster-autoscaler --selector=ray.io/node-type=head -o custom-columns=POD:metadata.name --no-headers
```

## Ray Dashboard port forwarding

List Ray services:
```
kubectl get rayservices
```

Port forward the head-svc to local 8265:
```
kubectl port-forward service/many-models-head-svc 8265:8265
```

You can then access the dashboard at http://localhost:8265


## Submit a job to the Ray Cluster

```
ray job submit --address http://localhost:8265 -- python -c "import ray; ray.init(); print(ray.cluster_resources())"
```