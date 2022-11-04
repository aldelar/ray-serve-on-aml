# Dynamic Many Models Online Serving

# Synopsis

This solution accelerator enables low latency scoring for many models scenarios. This solution leverages Ray Serve deployed in Azure Kubernetes Service (AKS).

The solution intent to scale from 100s to 10,000s of models assuming a hot cache of most frequently accessed models in the AKS cluster, and dynamic eviction/reloading of models.

A few key features:
- low latency when hot cache hit
- automatic evition based on cache optimization (hit based statistics)
- ability to update models on the fly at runtime when new model versions need to go live

# Architecture Basics

An AML Online Endpoint establishes the integration between AML and Ray Serve. A Ray Serve service deployed in KubeRay handles multiple deployments and dynamic loading of models to meet the endpoint demand.

# Repo Structure

```
models/				# test models to dry run the solution
src/
	core/
	deployment/

tests/				# test data and notebooks
```

# Setup

## Setup AKS Cluster
1) Create an AKS cluster in AML from the Portal using the Compute / Inference Clusters section. Select all defaults and proceed with the node type and cluster size desired.

2) Once created, register your cluster in kubectrl (we assume here you are running Ubuntu or WSL Ubuntu on Windows):
```
az aks get-credentials -n aldelarml0d866443c86 -g synapse
```

## Setup KubeRay

1) Check this section to grab the tag of the [latest stable version of KubeRay](https://github.com/ray-project/kuberay#use-yaml)

2) Set latest stable version variable (at moment of documentation, this was v0.3.0, replace as stable needed with the current latest version)

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