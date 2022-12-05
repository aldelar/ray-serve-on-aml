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
from ray.serve.handle import RayServeDeploymentHandle
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
        self.model = None
        self.reload_model()

    def __str__(self):
        return f"{self.model_name}"

    def reload_model(self, model_name : str = "iris_model"):
        """
        Load model from Redis Cache

        Parameters
        ----------
        model_name : string
        """
        # self.model_name = model_name
        self.model_name = "iris_model"
        redis_host = REDIS_HOST
        redis_key = REDIS_KEY
        
        r= redis.StrictRedis(host=redis_host, port=6380, password=redis_key, ssl=True)

        # Handle a case when model is not available in redis cache
        try: 
            self.model = pickle.loads(r.get(self.model_name))
        except: # catch error
            pass

    def reconfigure(self, config: Dict):
        """
        Reconfigure tentant map

        Parameters
        ---------
        config : Dict
        """
        model_name = config.get("tenant", "default")
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

        return {"deployment": self.__class__.__name__, "model": model_name, "prediction":prediction}


@serve.deployment(num_replicas=1, ray_actor_options={"num_cpus": 0.1})
class Deployment1(Deployment):
    """
    It is empty slot for a model
    """
    pass


@serve.deployment(num_replicas=1, ray_actor_options={"num_cpus": 0.1})
class Deployment2(Deployment):
    """
    It is empty slot for a model
    """
    pass


@serve.deployment(num_replicas=1, ray_actor_options={"num_cpus": 0.1})
class Deployment3(Deployment):
    """
    It is empty slot for a model
    """
    pass


@serve.deployment(num_replicas=1, ray_actor_options={"num_cpus": 0.1})
class Deployment4(Deployment):
    """
    It is empty slot for a model
    """
    pass


@serve.deployment(num_replicas=1, ray_actor_options={"num_cpus": 0.1})
class Deployment5(Deployment):
    """
    It is empty slot for a model
    """
    pass


@serve.deployment(num_replicas=1, ray_actor_options={"num_cpus": 0.1})
class Deployment6(Deployment):
    """
    It is empty slot for a model
    """
    pass


@serve.deployment(num_replicas=1, ray_actor_options={"num_cpus": 0.1})
class Deployment7(Deployment):
    """
    It is empty slot for a model
    """
    pass


@serve.deployment(num_replicas=1, ray_actor_options={"num_cpus": 0.1})
class Deployment8(Deployment):
    """
    It is empty slot for a model
    """
    pass


@serve.deployment(num_replicas=1, ray_actor_options={"num_cpus": 0.1})
class Deployment9(Deployment):
    """
    It is empty slot for a model
    """
    pass


@serve.deployment(num_replicas=1, ray_actor_options={"num_cpus": 0.1})
class Deployment10(Deployment):
    """
    It is empty slot for a model
    """
pass


@serve.deployment(num_replicas=1, ray_actor_options={"num_cpus": 0.1})
class Deploymentx(Deployment):
    """
    It is empty slot for a model
    """
    pass


@serve.deployment(num_replicas=1, ray_actor_options={"num_cpus": 0.1})
class SharedMemory:
    """ Class for SharedMemory
    Serve as shared memory object for tenant map and tenant queue
        - tenant map: dictionary holding maps of tenant and deployment class
        - tenant queue: prediction (work orders) request from clients 
    It manages number of models in memory and its type    
    Two types of model management 
        1. Dedicated - Fixed number of models will be in memory regardless of model use
        2. Dynamic - Fixed number of models will be in memory based on usage
    """
    def __init__(self, dynamic_queue_max_len : int = 8, dedicated_queue_max_len : int = 2):
        #to do:
        # self.dynamic_tenant_map
        # self.dedicated_tenant_map
        # The self.tenant_map becomes the combined map of all tenants to deployment. 
        # Operations to 
        self.dedicated_queue_max_len = dedicated_queue_max_len
        self.dynamic_queue_max_len = dynamic_queue_max_len

        self.dynamic_tenant_map = {}
        self.set_dynamic_tenant_map()

        self.dedicated_tenant_map = {}
        self.set_dedicated_tenant_map()

        self.dynamic_tenant_queue = deque(maxlen=dynamic_queue_max_len)

        for i in range(1,dynamic_queue_max_len+1): #todo configure the max number of available dynamic deployment slots 
            self.dynamic_tenant_queue.append(f"tenant{i}")

    def set_dynamic_tenant_map(self, map ={"tenant1":"deployment1",
                                            "tenant2":"deployment2",
                                            "tenant3":"deployment3",
                                            "tenant4":"deployment4",
                                            "tenant5":"deployment5",
                                            "tenant6":"deployment6",
                                            "tenant7":"deployment7",
                                            "tenant8":"deployment8"}):

        if len(map) <= self.dynamic_queue_max_len:
            self.dynamic_tenant_map = map
        else:
            # cut off elements 
            i = 0
            self.dynamic_tenant_map = map
            for item in map.items():
                i = i + 1
                if i > self.dynamic_queue_max_len:
                    self.dynamic_tenant_map.pop(item.key)
                else:        
                    continue
        
    def set_dedicated_tenant_map(self, map ={"tenant9":"deployment9",
                                            "tenant10":"deployment10"}):
        if len(map) <= self.dedicated_queue_max_len:
            self.dedicated_tenant_map = map
        else:
            # cut off elements 
            i = 0
            self.dedicated_tenant_map = map
            for item in map.items():
                i = i + 1
                if i > self.dedicated_queue_max_len:
                    self.dedicated_tenant_map.pop(item.key)
                else:        
                    continue

    def tenant_queue_remove(self, item):
        self.dynamic_tenant_queue.remove(item)

    def tenant_queue_append(self, item):
        self.dynamic_tenant_queue.append(item)

    def tenant_queue_popleft(self):
        return self.dynamic_tenant_queue.popleft()

    def tenant_map_pop(self, item):
        return self.dynamic_tenant_map.pop(item)

    # @app.post("/set_dynamic_tenant")
    def set_dynamic_tenant(self, tenant, deployment_name):
        self.dynamic_tenant_map[tenant]=deployment_name

    def lookup_deployment_name(self, tenant) -> str:
        # first look up dedicated pool, if not found then look up dynamic pool with default value.
        if tenant in self.dedicated_tenant_map:
            return self.dedicated_tenant_map.get(tenant)#, "default")

        if tenant in self.dynamic_tenant_map:
            return self.dynamic_tenant_map.get(tenant)#, "default")
        return None

    # def lookup_dynamic_deployment_name(self, tenant):
    #     return self.dynamic_tenant_map.get(tenant)#, "default")

    # def lookup_dedicated_deployment_name(self, tenant):
    #     return self.set_dedicated_tenant_map.get(tenant)#, "default")
    
    def get_dynamic_tenant_map(self):
        return self.dynamic_tenant_map

    def get_dedicated_tenant_map(self):
        return self.dedicated_tenant_map


@serve.deployment(num_replicas=1)
@serve.ingress(app)
class Dispatcher:
    """ Class for Dispatcher
    Route data to one of deployment (1-10) based on given tenant name
    
    Manage models - Load or unload models from memory
        - Load models from Redis Cache
        - Unload models from memory (free tentant from a deployment)
    
    deployment_map
    
    sharedmemory
    """
    def __init__(self, *deployments: RayServeDeploymentHandle,
                        deploymentx: RayServeDeploymentHandle,
                        sharedmemory: RayServeDeploymentHandle):
        # Create deployment_map with default
        self.deployment_map = {"default":deploymentx}

        i = 1
        for dep in deployments:
            self.deployment_map[f"deployment{i}"] = dep
            i = i + 1

        self.sharedmemory = sharedmemory

        self.q = queue.Queue(maxsize=2)
        threading.Thread(target=self.append, daemon=True).start()

    async def append(self): 
        while True:
            item_in_queue = self.q.get()
            #if the tenant is in dedicated pool, no need to update priority queue
            if item_in_queue in ray.get(await self.sharedmemory.get_dedicated_tenant_map.remote()):
                continue
            #handle the case where tenant is in dynamic pool
            if item_in_queue in ray.get(await self.sharedmemory.get_dynamic_tenant_map.remote()):
                #the tenant is already in the queue, just move it up to top position 
                ray.get(await self.sharedmemory.tenant_queue_remove.remote(item_in_queue))
                ray.get(await self.sharedmemory.tenant_queue_append.remote(item_in_queue))
            else: #if this tenant is not yet in the hot queue
                #  kick out old tenant
                out_item = ray.get(await self.sharedmemory.tenant_queue_popleft.remote())
                ray.get(await self.sharedmemory.tenant_queue_append.remote(item_in_queue))
                # update mapping table to route traffic of out_item to cold scoring
                current_deployment_name = ray.get(await self.sharedmemory.tenant_map_pop.remote(out_item))
                current_deployment = self.deployment_map.get(current_deployment_name)
                # promote the item_in_queue's deployment to hot
                ray.get(await current_deployment.reconfigure.remote({"tenant":item_in_queue}))
                #update mapping 
                ray.get(await self.sharedmemory.set_dynamic_tenant.remote(item_in_queue,current_deployment_name))


    @app.post("/update_dedicated_pool")
    async def process(self, item: TenantMapping):
        """
        """
        mapping = item.mapping
        #prepare dedicated deployment to cache the models
        for tenant, deployment_name in mapping.items():
            deployment = self.deployment_map.get(deployment_name)
            deployment.reconfigure.remote({"tenant":tenant})
            ray.get(await self.sharedmemory.set_dedicated_tenant_map.remote(mapping))
        return mapping

    @app.put("/reset_dynamic_pool")
    async def reset_dynamic_pool(self):
        """
        Reset dynamic pool with initial configuration
        """
        ray.get(await self.sharedmemory.set_dynamic_tenant_map.remote())
        return json.dumps(ray.get(await self.sharedmemory.get_dynamic_tenant_map.remote()))

    @app.post("/score")
    async def process(self, input: InputData):
        """
        Make prediction
        
        Parameters
        ----------
        input : InputData (tenant, data)
        """
        #assuming model name is same with tenant
        tenant = input.tenant
        data = input.data        
        deployment_name = ray.get(await self.sharedmemory.lookup_deployment_name.remote(tenant))
        # Get deployment (slot)
        deployment = self.deployment_map.get(deployment_name)
        # in case when a tenant is not found
        if deployment == None:
            return f"Can't find your tenant, {deployment_name} has not found. Maybe the tenant is not registered."

        result = ray.get(await deployment.predict.remote(data, tenant))
        # renew tenant lifetime
        self.q.put(tenant)
        return result

    @app.get("/get_deploymentmap")
    async def get_deploymentmap(self) -> str:
        """
        Get all the get_deploymentmap 
        """
        current_deploymentmap = []
        for deployment in self.deployment_map:
            current_deploymentmap.append(self.deployment_map[deployment].deployment_name)
        return json.dumps(current_deploymentmap)


    @app.get("/get_dynamic_tenantmap")
    async def get_tenantmap(self) -> str:
        """
        Get all the dynamic tenantmap and it's model name 
        """
        return json.dumps(ray.get(await self.sharedmemory.get_dynamic_tenant_map.remote()))

    @app.get("/get_dedicated_tenantmap")
    async def get_dedicated_tenantmap(self) -> str:
        """
        Get all the dedicated tenantmap and it's model name
        """
        return json.dumps(ray.get(await self.sharedmemory.get_dedicated_tenant_map.remote()))


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

dispatcher = Dispatcher.bind(deployment1,deployment2, deployment3, deployment4, deployment5,
                            deployment6, deployment7, deployment8, deployment9, deployment10,
                            deploymentx = deploymentx,
                            sharedmemory = sharedmemory)
