# ray-serve-on-aml

# SETUP

## Setup AKS Cluster
1) Create an AKS cluster in AML / Compute / Inference Clusters
2) Register your cluster in kubectrl:
```
az aks get-credentials -n aldelarml0d866443c86 -g synapse
```

## Setup KubeRay

1) Check the [latest stable version of KubeRay](https://github.com/ray-project/kuberay#use-yaml)

2) Set version variable

```
export KUBERAY_VERSION=v0.3.0
```

3) Install KubeRay Operator
```
kubectl create -k "github.com/ray-project/kuberay/ray-operator/config/crd?ref=${KUBERAY_VERSION}&timeout=90s"
```
```
helm install KubeRay Operator --namespace ray-system --create-namespace $(curl -s https://api.github.com/repos/ray-project/kuberay/releases/tags/${KUBERAY_VERSION} | grep '"browser_download_url":' | sort | grep -om1 'https.*helm-chart-kuberay-operator.*tgz')
```
4) Install Ray Cluster

Clone the kuberay repo (not in this repo, CD out of it)

```
cd /some_directory
git clone https://github.com/ray-project/kuberay.git
cd kuberay
```
```
cd helm-chart/ray/cluster
helm install ray-cluster --namespace ray-system --create-namespace .
```

5) Get the Ray Cluster head pod and launch the Ray dashboard
```
kubectl get pods --namespace ray-system
```
The output should look like this:
```
NAME                                           READY   STATUS    RESTARTS   AGE
kuberay-operator-84656d49d8-bmt6s              1/1     Running   0          16h
ray-cluster-kuberay-head-ccvw9                 1/1     Running   0          6m35s
ray-cluster-kuberay-worker-workergroup-9jsqx   1/1     Running   0          6m57s
```
Copy the NAME of the head node, it should look along the lines of: ray-cluster-kuberay-head-ccvw9

Forward the head node port to your localhost with this command (replace your head node name with the name collected from the command output above):
```
kubectl port-forward ray-cluster-kuberay-head-ccvw9 8265 --namespace ray-system
```
Open up your web browser to http://localhost:8265/ to check that the cluster is functioning properly.