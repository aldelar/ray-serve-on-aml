import ray
from ray import serve
from ray.serve.drivers import DAGDriver
from ray.serve.deployment_graph import InputNode
from typing import Dict, List
from starlette.requests import Request
from ray.serve.deployment_graph import ClassNode
# from azureml.core.model import Model
# from azureml.core import Workspace
# from azureml.core.authentication import ServicePrincipalAuthentication
import time
# import sklearn
# import joblib
import os
import threading, queue
from collections import deque
# from azure.ai.ml import MLClient
import redis
import pickle
# from azure.identity import ManagedIdentityCredential, ClientSecretCredential
import joblib

#
REDIS_HOST = os.getenv('REDIS_HOST')
REDIS_KEY =os.getenv('REDIS_KEY')

# Representing a deployment
# Assumption: model name = tenant name
class Deployment:

    def __init__(self):
        self.model_name= "default"
    
	def reload_model(self, model_name):
        redis_host = REDIS_HOST
        redis_key = REDIS_KEY
        r= redis.StrictRedis(host=redis_host, port=6380,
                                    password=redis_key, ssl=True)
        # if  not os.path.exists(model_name):
        # credential = ClientSecretCredential(tenant_id=tenant_id,client_id=client_id, client_secret=client_secret)
        # ml_client = MLClient(credential=credential,subscription_id=subscription_id,resource_group_name=resource_group, workspace_name=workspace_name)
        # model_operations = ml_client.models
        # print("return model" , model_operations.get("sklearn-iris", version=1))
        # ml_client.models.download("sklearn-iris","1",download_path=model_name)
        self.model = pickle.loads(r.get("iris_model"))
        # self.model = joblib.load(os.path.join(model_name, "sklearn-iris/model.joblib"))

    def reconfigure(self, config: Dict):
        model_name = config.get("tenant","default")
        self.reload_model(model_name)
        self.model_name = model_name
    
	def predict(self, data,model_name):
        #if model name is equal to deploy's configured model name, the model is already loaded
        if model_name != self.model_name:
            self.reload_model(model_name)
            time.sleep(0.5) # adding more latency to simulate loading large model
        prediction = self.model.predict(data)
        return {"deployment": self.__class__.__name__,"model": model_name, "prediction":prediction}

@serve.deployment(num_replicas=1)
class Deployment1(Deployment):
    pass

@serve.deployment(num_replicas=1)
class Deployment2(Deployment):
    pass

@serve.deployment(num_replicas=1)
class Deployment3(Deployment):
    pass

@serve.deployment(num_replicas=1)
class Deployment4(Deployment):
    pass

@serve.deployment(num_replicas=1)
class Deployment5(Deployment):
    pass

@serve.deployment(num_replicas=1)
class Deployment6(Deployment):
    pass

@serve.deployment(num_replicas=1)
class Deployment7(Deployment):
    pass

@serve.deployment(num_replicas=1)
class Deployment8(Deployment):
    pass

@serve.deployment(num_replicas=1)
class Deployment9(Deployment):
    pass

@serve.deployment(num_replicas=1)
class Deployment10(Deployment):
    pass

@serve.deployment(num_replicas=1)
class Deploymentx(Deployment):
    pass
#serve as shared memory object for tenant map and tenant queue

@serve.deployment(num_replicas=1)
class SharedMemory:

    def __init__(self):
        self.tenant_map = {"tenant1":"deployment1", "tenant2":"deployment2","tenant3":"deployment3","tenant4":"deployment4","tenant5":"deployment5"
        ,"tenant6":"deployment6","tenant7":"deployment7","tenant8":"deployment8","tenant9":"deployment9","tenant10":"deployment10"}
        self.tenant_queue = deque(maxlen=10)
        self.tenant_queue.append("tenant1")
        self.tenant_queue.append("tenant2")
        self.tenant_queue.append("tenant3")
        self.tenant_queue.append("tenant4")
        self.tenant_queue.append("tenant5")
        self.tenant_queue.append("tenant6")
        self.tenant_queue.append("tenant7")
        self.tenant_queue.append("tenant8")
        self.tenant_queue.append("tenant9")
        self.tenant_queue.append("tenant10")

    def tenant_queue_remove(self, item):
        self.tenant_queue.remove(item)

    def tenant_queue_append(self, item):
        self.tenant_queue.append(item)

    def tenant_queue_popleft(self):
        return self.tenant_queue.popleft()

    def tenant_map_pop(self, item):
        return self.tenant_map.pop(item)

    def set_tenant_map(self, tenant, deployment_name):
        self.tenant_map[tenant]=deployment_name

    def get_deployment_name(self, tenant):
        return self.tenant_map.get(tenant, "default")

    def get_tenant_map(self):
        return self.tenant_map

@serve.deployment(num_replicas=2)
class Dispatcher:

    def __init__(self, deployment1: ClassNode, deployment2: ClassNode, deployment3: ClassNode, deployment4: ClassNode, deployment5: ClassNode, deployment6: ClassNode, deployment7: ClassNode
    , deployment8: ClassNode, deployment9: ClassNode, deployment10: ClassNode, deploymentx: ClassNode,sharedmemory: ClassNode):
        self.deployment_map = {"deployment1":deployment1, "deployment2":deployment2,"deployment3":deployment3,
        "deployment4":deployment4, "deployment5":deployment5,"deployment6":deployment6,"deployment7":deployment7,"deployment8":deployment8,"deployment9":deployment9,"deployment10":deployment10, "default":deploymentx}
        self.sharedmemory = sharedmemory
        self.q = queue.Queue()
        threading.Thread(target=self.append, daemon=True).start()

    def append(self):
        while True:
            new_item = self.q.get()
            if new_item in ray.get(self.sharedmemory.get_tenant_map.remote()):
                #the tenant is already in the queue, just move it up to higher priority
                ray.get(self.sharedmemory.tenant_queue_remove.remote(new_item))
                ray.get(self.sharedmemory.tenant_queue_append.remote(new_item))
            else: #if this tenant is not yet in the hot queue
                #  kick out old tenant
                out_item = ray.get(self.sharedmemory.tenant_queue_popleft.remote())
                ray.get(self.sharedmemory.tenant_queue_append.remote(new_item))
                # update mapping table to route traffic of out_item to cold scoring
                current_deployment_name = ray.get(self.sharedmemory.tenant_map_pop.remote(out_item))
                current_deployment = self.deployment_map.get(current_deployment_name)
                # promote the new_item's deployment to hot
                ray.get(current_deployment.reconfigure.remote({"tenant":new_item}))
                #update mapping 
                ray.get(self.sharedmemory.set_tenant_map.remote(new_item,current_deployment_name))

    def process(self, raw_input):
        #assuming model name is same with tenant
        tenant = raw_input.get('tenant')
        # threading.Thread(target=self.append, daemon=True, args=(tenant)).start()
        data = raw_input.get("data")
        deployment_name = ray.get(self.sharedmemory.get_deployment_name.remote(tenant))
        deployment= self.deployment_map.get(deployment_name)
        result = ray.get(deployment.predict.remote(data, tenant))
        result["deployment_map"] = ray.get(self.sharedmemory.get_tenant_map.remote())
        self.q.put(tenant)

        return result

async def json_resolver(request: Request) -> List:
    return await request.json()

with InputNode() as message:
    # message, amount = query[0], query[1]
    deployment1 = Deployment1.bind()
    deployment2 = Deployment2.bind()
    deployment3 = Deployment3.bind()
    deployment4 = Deployment4.bind()
    deployment5 = Deployment5.bind()
    deployment6 = Deployment6.bind()
    deployment7 = Deployment7.bind()
    deployment8 = Deployment8.bind()
    deployment9 = Deployment9.bind()
    deployment10 = Deployment10.bind()
    deploymentx = Deploymentx.bind()
    sharedmemory = SharedMemory.bind()
    dispatcher = Dispatcher.bind(deployment1, deployment2,deployment3,deployment4, deployment5,deployment6,deployment7, deployment8,deployment9,deployment10,deploymentx,sharedmemory)
    output_message = dispatcher.process.bind(message)

deployment_graph = DAGDriver.bind(output_message, http_adapter=json_resolver)