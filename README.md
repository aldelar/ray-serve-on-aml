# Dynamic Many Models Online Serving

# Synopsis

This solution accelerator enables low latency scoring for many models scenarios in a cost efficient manner. This solution leverages Ray Serve deployed in Azure Kubernetes Service (AKS), backed by models trained in Azure Machine Learning (AML) and stored in the AML Model Registry.

The solution intent to scale from 100s to 10,000s of models assuming a hot cache of most frequently accessed models in the AKS cluster and dynamic eviction/reloading of models from a warn cache (Azure Redis) and cold cache (AML Model Registry).

A few key features:
- low latency when hot cache hit
- automatic evition based on cache optimization (hit based statistics)
- ability to update models on the fly at runtime when new model versions need to go live

# Overall Architecture

![ServiceComponent](/images/ManyModel_RayServe_ServiceComponents.png)

A Ray Serve service deployed in KubeRay handles multiple deployments and dynamic loading of models to meet the endpoint demand.

# Repo Structure

```bash
images/             # Images for the repo
models/				# test models to dry run the solution
src/
    core/           # ray cluster service code
    deployment/     # ray service deployment descriptor
    IaC/            # Infrastructure as Code
    tests/			# test data and notebooks
```

# Setup

## Environment

You'll need the following tools:
- PC (running Linux or [Windows Subsystem for Linux](https://learn.microsoft.com/en-us/windows/wsl/install)) or Mac
- Azure Subscription
- Azure account with contributor or owner of a resource group
- Azure [CLI](https://learn.microsoft.com/en-us/cli/azure/install-azure-cli) (or CloudShell)
- kubectl 

## Azure Login

```bash
az login --tenant {replacewithYOURTENANTID}
az account set -s {replacewithYOURAZURESUBSCRIPTIONID}
```

## Clone Repo

```bash
git clone https://github.com/aldelar/ray-serve-on-aml.git
```

## Create Azure Resources

After login to Azure you can run the Azure CLI script to provision the necessary Azure rescoures:
- Azure Resource Group
- Azure Machine Learning
- Azure Kubernetes Services

Execute `src/IaC/IaC_0_ray_serve_on_aml.azcli` to create your Azure resources:
```bash
./ray-serve-on-aml/src/IaC/IaC_0_ray_serve_on_aml.azcli
```

Here are some key elements of this script:

1) Creation of an AKS cluster:

```bash
az aks create -n rayserve001 -g ml --node-count 2  -s standard_dc16s_v3 --enable-managed-identity --generate-ssh-keys
```

2) Registration of your cluster in kubectrl:

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
kubectl create -k "github.com/ray-project/kuberay/ray-operator/config/default?ref=${KUBERAY_VERSION}&timeout=90s"
```

```bash
kubectl apply -f https://raw.githubusercontent.com/ray-project/kuberay/release-0.3/ray-operator/config/samples/ray-cluster.autoscaler.yaml
```
## Deploy the Many Models Scoring Service

1) Deploy with kubectl

```bash
kubectl apply -f ./ray-serve-on-aml/src/deployment/ray_service.yaml
```

2) Check the status of the deployed service

Run this command multiple times until all services are 'HEALTHY':
```bash
kubectl describe rayservices many-models
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
3) Expose the service 

```bash
kubectl expose service many-models-serve-svc --type=LoadBalancer --name many-models-loadbalancer
```

4) Get the public IP of the load balancer service
```bash
kubectl describe services many-models-loadbalancer
```
The output should look like this. Grab the 'LoadBalancer Ingress' IP:

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

## Tests

A test notebook is located at 'src/tests/test_scoring.ipynb'. Run this notebook using a kernel based on the provided conda environment file located at 'src/tests/test_conda.yml'.

Create the conda environment and activate it in your Jupyter notebook laptop/server:
``` bash
conda env create -f ./src/tests/test_conda.yml
conda activate ray-serve-on-aml-test
```

Here's the content of this notebook:

```python
import json
import urllib.request
import random
import pandas as pd

base_uri ='http://IP_OF_LOAD_BALANCER:8000'

dataset = pd.read_csv("https://azuremlexamples.blob.core.windows.net/datasets/iris.csv")
X=dataset[['sepal_length','sepal_width','petal_length','petal_width']]

def score(X, tenant):
    # tenant = random.choices(["tenant1","tenant2", "tenant3","tenant4","tenant5","tenant6","tenant7", "tenant8","tenant9"])[0]
    len = random.randint(2,50)
    data = {"tenant":tenant, "data": X.head(len).to_numpy().tolist()}
    body = str.encode(json.dumps(data))
    url = f'{base_uri}/score'
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

def updated_dedicated_pool(mapping):

    body = str.encode(json.dumps({"mapping":mapping}))
    url = f'{base_uri}/update_dedicated_pool'
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

Test scoring:
```python
score(X, "tenant29")
```

The output should look like this:

```json
{'deployment': 'Deploymentx', 'model': 'tenant13', 'prediction': [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0], 'deployment_map': {'tenant1': 'deployment1', 'tenant2': 'deployment2', 'tenant3': 'deployment3', 'tenant4': 'deployment4', 'tenant5': 'deployment5', 'tenant6': 'deployment6', 'tenant7': 'deployment7', 'tenant8': 'deployment8', 'tenant9': 'deployment9', 'tenant10': 'deployment10'}}
```