# Dynamic Many Models Online Serving

# Synopsis

This solution accelerator enables low latency scoring for many models scenarios. This solution leverages Ray Serve deployed in Azure Kubernetes Service (AKS).

The solution intent to scale from 100s to 10,000s of models assuming a hot cache of most frequently accessed models in the AKS cluster, and dynamic eviction/reloading of models.

A few key features:
- low latency when hot cache hit
- automatic evition based on cache optimization (hit based statistics)
- ability to update models on the fly at runtime when new model versions need to go live

# Architecture Basics

![ServiceComponent](/images/ManyModel_RayServe_ServiceComponents.png)

An AML Online Endpoint establishes the integration between AML and Ray Serve. A Ray Serve service deployed in KubeRay handles multiple deployments and dynamic loading of models to meet the endpoint demand.

# Repo Structure

```bash
models/				# test models to dry run the solution
src/
	core/
	deployment/

tests/				# test data and notebooks
```

# Setup

## Requirements

Need following tools

- Azure Subscription
- Azure account with contributor or owner of a resource group
- Azure Cli (or CloudShell)

## Login

```bash
az login --tenant {replacewithYOURTENANTID}
az account set -s {replacewithYOURAZURESUBSCRIPTIONID}
```

## Clone this repo

```bash
git clone https://github.com/aldelar/ray-serve-on-aml.git
```

## Create Resources

After login to Azure you can run azcli script to provision Azure rescoures
- Azure Resource Group
- Azure Machine Learning
- Azure Kubernetes Services

Run Azcli script
```bash
./src/IaC/IaC_0_ray_serve_on_aml.azcli
```

### Setup AKS Cluster

    Following code will be executed in the `IaC_0_ray_serve_on_aml.azcli` script

    > 1) Create an AKS cluster 

        ```bash
        az aks create -n rayserve001 -g ml --node-count 2  -s standard_dc16s_v3 --enable-managed-identity --generate-ssh-keys
        ```

    > 2) Once created, register your cluster in kubectrl (we assume here you are running Ubuntu or WSL Ubuntu on Windows):

        ```bash
        az aks get-credentials -n rayserve001 -g ml
        ```

## Setup KubeRay for Ray Serve

1) Check this section to grab the tag of the [latest stable version of KubeRay](https://github.com/ray-project/kuberay#use-yaml)

2) Set latest stable version variable (at moment of documentation, this was v0.3.0, replace as stable needed with the current latest version)

```bash
export KUBERAY_VERSION=v0.3.0
```

3) Install KubeRay Operator

```bash
kubectl create -k "github.com/ray-project/kuberay/ray-operator/config/crd?ref=${KUBERAY_VERSION}"
```

```bash
kubectl apply -k "github.com/ray-project/kuberay/manifests/base?ref=${KUBERAY_VERSION}"

```
4) Deploy many models serving application


```bash
cd /src/deployment
```

```bash
kubectl apply -f ray_service.yaml
```
check the status of the deployed application

```bash
kubectl describe rayservice many-models-serving
```

The output should look like this

```text
    Serve Deployment Statuses:
      Health Last Update Time:  2022-11-04T18:48:05Z
      Last Update Time:         2022-11-04T18:48:05Z
      Name:                     Deployment1
      Status:                   HEALTHY
      Health Last Update Time:  2022-11-04T18:48:05Z
      Last Update Time:         2022-11-04T18:48:05Z
      Name:                     Deployment2
      Status:                   HEALTHY
      Health Last Update Time:  2022-11-04T18:48:05Z
      Last Update Time:         2022-11-04T18:48:05Z
      Name:                     Deployment3
      Status:                   HEALTHY
      Health Last Update Time:  2022-11-04T18:48:05Z
      Last Update Time:         2022-11-04T18:48:05Z
      Name:                     Deployment4
      Status:                   HEALTHY
      Health Last Update Time:  2022-11-04T18:48:05Z
      Last Update Time:         2022-11-04T18:48:05Z
      Name:                     Deployment5
      Status:                   HEALTHY
      Health Last Update Time:  2022-11-04T18:48:05Z
      Last Update Time:         2022-11-04T18:48:05Z
      Name:                     Deployment6
      Status:                   HEALTHY
      Health Last Update Time:  2022-11-04T18:48:05Z
      Last Update Time:         2022-11-04T18:48:05Z
      Name:                     Deployment7
      Status:                   HEALTHY
      Health Last Update Time:  2022-11-04T18:48:05Z
      Last Update Time:         2022-11-04T18:48:05Z
      Name:                     Deployment8
      Status:                   HEALTHY
      Health Last Update Time:  2022-11-04T18:48:05Z
      Last Update Time:         2022-11-04T18:48:05Z
      Name:                     Deployment9
      Status:                   HEALTHY
      Health Last Update Time:  2022-11-04T18:48:05Z
      Last Update Time:         2022-11-04T18:48:05Z
      Name:                     Deployment10
      Status:                   HEALTHY
      Health Last Update Time:  2022-11-04T18:48:05Z
      Last Update Time:         2022-11-04T18:48:05Z
      Name:                     Deploymentx
      Status:                   HEALTHY
      Health Last Update Time:  2022-11-04T18:48:05Z
      Last Update Time:         2022-11-04T18:48:05Z
      Name:                     SharedMemory
      Status:                   HEALTHY
      Health Last Update Time:  2022-11-04T18:48:05Z
      Last Update Time:         2022-11-04T18:48:05Z
      Name:                     Dispatcher
      Status:                   HEALTHY
      Health Last Update Time:  2022-11-04T18:48:05Z
      Last Update Time:         2022-11-04T18:48:05Z
      Name:                     DAGDriver
      Status:                   HEALTHY
```
5) Expose the service 

```bash
kubectl expose service many-models-serve-svc --type=LoadBalancer --name many-models-loadbalancer
```

Get the public IP
```bash
kubectl describe services many-models-loadbalancer
```
The output should look like this

```text
Name:                     many-models-loadbalancer
Namespace:                default
Labels:                   ray.io/serve=many-models-serve
                          ray.io/service=many-models
Annotations:              <none>
Selector:                 ray.io/cluster=many-models-raycluster-b95qb,ray.io/serve=true
Type:                     LoadBalancer
IP Family Policy:         SingleStack
IP Families:              IPv4
IP:                       10.0.115.56
IPs:                      10.0.115.56
LoadBalancer Ingress:     40.91.121.97
Port:                     <unset>  8000/TCP
TargetPort:               8000/TCP
NodePort:                 <unset>  32458/TCP
Endpoints:                <none>
Session Affinity:         None
```
6. Perform testing

```python
import json
import urllib.request
import random
def score(X, tenant):
    # tenant = random.choices(["tenant1","tenant2", "tenant3","tenant4","tenant5","tenant6","tenant7", "tenant8","tenant9"])[0]

    len = random.randint(2,50)
    data = {"tenant":tenant, "data": X.head(len).to_numpy().tolist()}

    body = str.encode(json.dumps(data))

    url = 'http://URL_OF_LOAD_BALANCER:8000'


    headers = {'Content-Type':'application/json'}

    req = urllib.request.Request(url, body, headers)

    try:
        response = urllib.request.urlopen(req)

        result = response.read()
        print(json.loads(result))
    except urllib.error.HTTPError as error:
        print("The request failed with status code: " + str(error.code))

        # Print the headers - they include the requert ID and the timestamp, which are useful for debugging the failure
        print(error.info())
        print(error.read().decode("utf8", 'ignore'))

```

```python
import pandas as pd
from sklearn.preprocessing import LabelEncoder
import joblib
dataset = pd.read_csv("https://azuremlexamples.blob.core.windows.net/datasets/iris.csv")
X= dataset[['sepal_length','sepal_width','petal_length','petal_width']]
```

Test scoring
```python
score(X, "tenant29")
```

Output should look like this

```json
{'deployment': 'Deploymentx', 'model': 'tenant13', 'prediction': [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0], 'deployment_map': {'tenant1': 'deployment1', 'tenant2': 'deployment2', 'tenant3': 'deployment3', 'tenant4': 'deployment4', 'tenant5': 'deployment5', 'tenant6': 'deployment6', 'tenant7': 'deployment7', 'tenant8': 'deployment8', 'tenant9': 'deployment9', 'tenant10': 'deployment10'}}
```