import time
import json
# import sklearn
# import joblib
import os
import threading, queue
from collections import deque
import redis
import pickle
import joblib
import ray
from ray import serve
from ray.serve.drivers import DAGDriver
from ray.serve.deployment_graph import InputNode
from typing import Dict, List
from starlette.requests import Request
from ray.serve.deployment_graph import ClassNode
from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Union, Dict
from dotenv import load_dotenv

# Use dotEnv to load 
load_dotenv()
app = FastAPI()

# Use dotEnv to load 
REDIS_HOST = os.environ["REDIS_HOST"]
REDIS_KEY = os.environ["REDIS_KEY"] 


#schema for fastapi to parse data from http request
class InputData(BaseModel):
    data: List[List[float]]
    tenant: str


class TenantMapping(BaseModel):
    mapping:dict


#repsenting a deployment scoring. Assumption is model name = tenant name for simpicity.
class Deployment:
    """ Class for Deployment
    Default model_name is 'default'
    """
    def __init__(self):
        self.model_name= "default"

    def reload_model(self, model_name):
        """
        Load model from Redis Cache

        Parameters
        ----------
        model_name : string
        """
        
        redis_host = REDIS_HOST
        redis_key = REDIS_KEY
        
        r= redis.StrictRedis(host=redis_host, port=6380, password=redis_key, ssl=True)

        # Handle a case when model is not available in redis cache
        try: 
            self.model = pickle.loads(r.get("iris_model"))
        except: # catch error
            pass

    def reconfigure(self, config: Dict):
        """
        Reconfigure tentant map

        Parameters
        ---------
        config : Dict
        """
        model_name = config.get("tenant","default")
        self.reload_model(model_name)
        self.model_name = model_name

    def predict(self, data, model_name) -> dict:
        """
        Make a prediction

        Parameters
        ----------
        data : 
        model_name : string

        Return
        ------
        Prediction results
        """
        #if model name is equal to deploy's configured model name, the model is already loaded
        if model_name != self.model_name:
            self.reload_model(model_name)
            time.sleep(0.5) # adding more latency to simulate loading large model
        prediction = self.model.predict(data)

        return {"deployment": self.__class__.__name__,"model": model_name, "prediction":prediction}


@serve.deployment(num_replicas=1, ray_actor_options={"num_cpus": 0.1})
class Deployment1(Deployment):
    pass


@serve.deployment(num_replicas=1, ray_actor_options={"num_cpus": 0.1})
class Deployment2(Deployment):
    pass


@serve.deployment(num_replicas=1, ray_actor_options={"num_cpus": 0.1})
class Deployment3(Deployment):
    pass


@serve.deployment(num_replicas=1, ray_actor_options={"num_cpus": 0.1})
class Deployment4(Deployment):
    pass


@serve.deployment(num_replicas=1, ray_actor_options={"num_cpus": 0.1})
class Deployment5(Deployment):
    pass


@serve.deployment(num_replicas=1, ray_actor_options={"num_cpus": 0.1})
class Deployment6(Deployment):
    pass


@serve.deployment(num_replicas=1, ray_actor_options={"num_cpus": 0.1})
class Deployment7(Deployment):
    pass


@serve.deployment(num_replicas=1, ray_actor_options={"num_cpus": 0.1})
class Deployment8(Deployment):
    pass


@serve.deployment(num_replicas=1, ray_actor_options={"num_cpus": 0.1})
class Deployment9(Deployment):
    pass


@serve.deployment(num_replicas=1, ray_actor_options={"num_cpus": 0.1})
class Deployment10(Deployment):
    pass


@serve.deployment(num_replicas=1, ray_actor_options={"num_cpus": 0.1})
class Deploymentx(Deployment):
    pass


#serve as shared memory object for tenant map and tenant queue
@serve.deployment(num_replicas=1, ray_actor_options={"num_cpus": 0.1})
class SharedMemory:
    """ Class for SharedMemory
    Manage models - Load or unload models from memory
    Two types of model management 
        1. Dedicated - Fixed number of models will be in memory regardless of model use
        2. Dynamic - Fixed number of models will be in memory based on usage
    """
    def __init__(self):
        #to do:
        # self.dynamic_tenant_map
        # self.dedicated_tenant_map
        # The self.tenant_map becomes the combined map of all tenants to deployment. 
        # Operations to 
        self.dynamic_tenant_map = {}
        self.set_dynamic_tenant_map()
        
        self.dedicated_tenant_map = {}
        self.set_dedicated_tenant_map()

        self.dynamic_tenant_queue = deque(maxlen=8)
        for i in range(1,9): #todo configure the max number of available dynamic deployment slots 
            self.dynamic_tenant_queue.append(f"tenant{i}")

    def set_dynamic_tenant_map(self, map ={"tenant1":"deployment1",
                                            "tenant2":"deployment2",
                                            "tenant3":"deployment3",
                                            "tenant4":"deployment4",
                                            "tenant5":"deployment5",
                                            "tenant6":"deployment6",
                                            "tenant7":"deployment7",
                                            "tenant8":"deployment8"}):
        self.dynamic_tenant_map = map

    def set_dedicated_tenant_map(self, map ={"tenant9":"deployment9",
                                            "tenant10":"deployment10"}):
        self.dedicated_tenant_map = map

    def tenant_queue_remove(self, item):
        self.dynamic_tenant_queue.remove(item)

    def tenant_queue_append(self, item):
        self.dynamic_tenant_queue.append(item)

    def tenant_queue_popleft(self):
        return self.dynamic_tenant_queue.popleft()

    def tenant_map_pop(self, item):
        return self.dynamic_tenant_map.pop(item)

    def set_dynamic_tenant(self, tenant, deployment_name):
        self.dynamic_tenant_map[tenant]=deployment_name

    def lookup_deployment_name(self, tenant):
        # first look up dedicated pool, if not found then look up dynamic pool with default value.
        if tenant in self.dedicated_tenant_map:
            return self.dedicated_tenant_map.get(tenant, "default")
        return self.dynamic_tenant_map.get(tenant, "default")

    def lookup_dynamic_deployment_name(self, tenant):
        return self.dynamic_tenant_map.get(tenant, "default")

    def lookup_dedicated_deployment_name(self, tenant):
        return self.set_dedicated_tenant_map.get(tenant, "default")
        
    def get_dynamic_tenant_map(self):
        return self.dynamic_tenant_map

    def get_dedicated_tenant_map(self):
        return self.dedicated_tenant_map


@serve.deployment(num_replicas=2)
@serve.ingress(app)
class Dispatcher:
    """ Class for Dispatcher
    Route data to one of deployment (1-10) based on given tenant name
    deployment_map
    sharedmemory
    """
    # def __init__(self,
    #             *modelDeployment: ClassNode,
    #             deploymentx : ClassNode,
    #             sharedmemory: ClassNode):
    def __init__(self, deployment1: ClassNode, deployment2: ClassNode, 
                    deployment3: ClassNode, deployment4: ClassNode,
                    deployment5: ClassNode, deployment6: ClassNode,
                    deployment7: ClassNode, deployment8: ClassNode,
                    deployment9: ClassNode, deployment10: ClassNode,
                    deploymentx: ClassNode, sharedmemory: ClassNode):


        # numModels = 1
        # self.deployment_map["default"] = deploymentx

        # for modelDeployment_ in modelDeployment:
        #     self.deployment_map[f"deployment{numModels}"] = modelDeployment_
        #     numModels = numModels + 1

        self.deployment_map = {
            "deployment1":deployment1,
            "deployment2":deployment2,
            "deployment3":deployment3,
            "deployment4":deployment4,
            "deployment5":deployment5,
            "deployment6":deployment6,
            "deployment7":deployment7,
            "deployment8":deployment8,
            "deployment9":deployment9,
            "deployment10":deployment10,
            "default":deploymentx}

        self.sharedmemory = sharedmemory

        self.q = queue.Queue()
        threading.Thread(target=self.append, daemon=True).start()

    def append(self): 
        while True:
            new_item = self.q.get()
            #if the tenant is in dedicated pool, no need to update priority queue
            if new_item in ray.get(self.sharedmemory.get_dedicated_tenant_map.remote()):
                continue
            #handle the case where tenant is in dynamic pool
            if new_item in ray.get(self.sharedmemory.get_dynamic_tenant_map.remote()):
                #the tenant is already in the queue, just move it up to top position 
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
                ray.get(self.sharedmemory.set_dynamic_tenant.remote(new_item,current_deployment_name))


    @app.post("/update_dedicated_pool")
    def process(self, item: TenantMapping):
        """
        """
        mapping = item.mapping
        #prepare dedicated deployment to cache the models
        for tenant, deployment_name in mapping.items():
            deployment= self.deployment_map.get(deployment_name)
            deployment.reconfigure.remote({"tenant":tenant})
            ray.get(self.sharedmemory.set_dedicated_tenant_map.remote(mapping))
        return mapping

    @app.post("/score")
    def process(self, input: InputData):
        """
        Make prediction
        
        Parameters
        ----------
        input : InputData
        """
        #assuming model name is same with tenant
        tenant = input.tenant
        data = input.data        
        deployment_name = ray.get(self.sharedmemory.lookup_deployment_name.remote(tenant))
        deployment= self.deployment_map.get(deployment_name)
        result = ray.get(deployment.predict.remote(data, tenant))
        result["deployment_map"] = ray.get(self.sharedmemory.get_dynamic_tenant_map.remote())
        self.q.put(tenant)
        return result

    @app.get("/get_dynamic_tenantmap")
    def get_tenantmap(self) -> str:
        """
        Get all the dynamic tenantmap and it's model name 
        """
        return json.dumps(ray.get(self.sharedmemory.get_dynamic_tenant_map.remote()))

    @app.get("/get_dedicated_tenantmap")
    def get_dedicated_tenantmap(self) -> str:
        """
        Get all the dedicated tenantmap and it's model name
        """
        return json.dumps(ray.get(self.sharedmemory.get_dedicated_tenant_map.remote()))

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
# deployments = [deployment1, deployment2, deployment3, deployment4, deployment5, deployment6, deployment7, deployment8, deployment9, deployment10]

dispatcher = Dispatcher.bind(deployment1, deployment2, deployment3, deployment4, deployment5, deployment6, deployment7, deployment8, deployment9, deployment10, deploymentx, sharedmemory)
