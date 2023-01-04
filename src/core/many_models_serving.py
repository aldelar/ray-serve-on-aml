import ray
from ray import serve
from ray.serve.drivers import DAGDriver
from ray.serve.deployment_graph import InputNode
from ray.serve.deployment_graph import ClassNode

from typing import Dict, List, Union
from starlette.requests import Request
from pydantic import BaseModel
from collections import deque

import time, os, threading, queue
import redis

# import asyncio
# def get_or_create_eventloop():
#     try:
#         return asyncio.get_event_loop()
#     except RuntimeError as ex:
#         if "There is no current event loop in thread" in str(ex):
#             loop = asyncio.new_event_loop()
#             asyncio.set_event_loop(loop)
#             return asyncio.get_event_loop()

# create FastAPI app
from fastapi import FastAPI
app = FastAPI()

# Use dotEnv to load config
from dotenv import load_dotenv
load_dotenv()
REDIS_HOST = os.environ["REDIS_HOST"]
REDIS_KEY = os.environ["REDIS_KEY"] 

# Schema for FastAPI to parse data from http request
class InputData(BaseModel):
    data: List[List[float]]
    tenant:str
class TenantMapping(BaseModel):
    mapping:dict

# custom model handler for the implementation, used by the Deployment
import custom_model_handler as model_handler
# Deployment: assumption is model name = tenant name for simplicity
class Deployment:

    def __init__(self):
        self.model_name = ""
        self.redis_host = REDIS_HOST
        self.redis_key = REDIS_KEY
    
    def load_model(self, model_name):
        r = redis.StrictRedis(host=self.redis_host, port=6380, password=self.redis_key, ssl=True)
        # delegation to model_handler
        self.model = model_handler.load_model(r.get(model_name))

    def configure(self, config: Dict):
        model_name = config.get("tenant","default") # assuming model name = tenant name
        self.model_name = model_name
        self.load_model(model_name)
    
    def predict(self, data, model_name):
        # if model name is equal to deployed configured model name, the model is already loaded
        if model_name != self.model_name:
            self.load_model(model_name)
            time.sleep(0.5) # adding more latency to simulate loading large model
        # delegation to model_handler
        prediction = model_handler.predict(self.model,data)
        return {"deployment": self.__class__.__name__, "model": model_name, "prediction": prediction}

# Definitions of all Deployments to serve models
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
class Deploymentx(Deployment):
    pass

# Deployment for the Management service (tenant map, tenant queue, model management)
@serve.deployment(num_replicas=1, ray_actor_options={"num_cpus": 0.1})
@serve.ingress(app)
class Management:
    
    def __init__(self):
        self.model_registry_tag = "latest"
        # TODO:
        # self.dynamic_tenant_map
        # self.pinned_tenant_map
        # The self.tenant_map becomes the combined map of all tenants to deployment. 
        self.dynamic_tenant_map = {}
        self.set_dynamic_tenant_map()
        self.pinned_tenant_map = {}
        self.set_pinned_tenant_map()
        self.dynamic_tenant_queue = deque(maxlen=3)
        for i in range(1,3):
            #TODO: configure the max number of available dynamic deployment slots
            self.dynamic_tenant_queue.append(f"tenant{i}")
    
    @app.post("/set_aml_registry_tag")
    def set_aml_registry_tag(self, request: Request):
        self.model_registry_tag = request.json()["tag"]
        return {"status": "success"}
    
    @app.post("/refresh_models")
    def refresh_models(self):
        # TODO:
        # refresh all models in redis cache
        # refresh all models in the pinned_tenant_map
        # refresh all models in the dynamic_tenant_map
        return {"status": "success"}

    def set_pinned_tenant_map(self, map ={"tenant1":"deployment1"}):
        self.pinned_tenant_map = map

    def set_dynamic_tenant_map(self, map ={"tenant2":"deployment2","tenant3":"deployment3"}):
        self.dynamic_tenant_map = map

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
        # first look up pinned pool, if not found then look up dynamic pool with default value.
        if tenant in self.pinned_tenant_map:
            return self.pinned_tenant_map.get(tenant, "default")
        return self.dynamic_tenant_map.get(tenant, "default")

    def lookup_dynamic_deployment_name(self, tenant):
        return self.dynamic_tenant_map.get(tenant, "default")

    def lookup_pinned_deployment_name(self, tenant):
        return self.set_pinned_tenant_map.get(tenant, "default")

    def get_dynamic_tenant_map(self):
        return self.dynamic_tenant_map

    def get_pinned_tenant_map(self):
        return self.pinned_tenant_map

# Deployment for Dispatcher service
@serve.deployment(num_replicas=2)
@serve.ingress(app)
class Dispatcher:

    def __init__(self, management: ClassNode, deployment1: ClassNode, deployment2: ClassNode, deployment3: ClassNode, deploymentx: ClassNode):
        self.management = management
        self.deployment_map = {"deployment1":deployment1, "deployment2":deployment2,"deployment3":deployment3, "default":deploymentx}
        self.q = queue.Queue()
        threading.Thread(target=self.append, daemon=True).start()

    def append(self):
        while True:
            new_item = self.q.get()
            # if the tenant is in pinned pool, no need to update priority queue
            if new_item in ray.get(self.management.get_pinned_tenant_map.remote()):
                continue
            # handle the case where tenant is in dynamic pool
            if new_item in ray.get(self.management.get_dynamic_tenant_map.remote()):
                # the tenant is already in the queue, just move it up to top position 
                ray.get(self.management.tenant_queue_remove.remote(new_item))
                ray.get(self.management.tenant_queue_append.remote(new_item))
            else: # if this tenant is not yet in the dynamic pool
                # kick out oldest cached tenant in dynamic pool
                out_item = ray.get(self.management.tenant_queue_popleft.remote())
                ray.get(self.management.tenant_queue_append.remote(new_item))
                # update mapping table to route traffic of out_item to cold scoring
                current_deployment_name = ray.get(self.management.tenant_map_pop.remote(out_item))
                current_deployment = self.deployment_map.get(current_deployment_name)
                # promote the new_item's deployment to hot
                ray.get(current_deployment.configure.remote({"tenant":new_item}))
                # update mapping 
                ray.get(self.management.set_dynamic_tenant.remote(new_item,current_deployment_name))

    @app.post("/update_pinned_pool")
    def process(self, item: TenantMapping):
        mapping = item.mapping
        # prepare pinned deployment to cache the models
        for tenant, deployment_name in mapping.items():
            deployment= self.deployment_map.get(deployment_name)
            deployment.configure.remote({"tenant":tenant})
            ray.get(self.management.set_pinned_tenant_map.remote(mapping))
        return mapping
    
    @app.post("/score")
    def process(self, input: InputData):
        tenant = input.tenant
        model_name = tenant # assuming model name = tenant name
        data = input.data        
        deployment_name = ray.get(self.management.lookup_deployment_name.remote(tenant))
        deployment = self.deployment_map.get(deployment_name)
        result = ray.get(deployment.predict.remote(data, model_name))
        result["deployment_map"] = ray.get(self.management.get_dynamic_tenant_map.remote())
        self.q.put(tenant)
        return result

# instantiate model deployments
deployment1 = Deployment1.bind()
deployment2 = Deployment2.bind()
deployment3 = Deployment3.bind()
deploymentx = Deploymentx.bind()
# instantiate management service
management = Management.bind()
# instantiate Dispatcher service and bind to all other services
dispatcher = Dispatcher.bind(management,deployment1,deployment2,deployment3,deploymentx)