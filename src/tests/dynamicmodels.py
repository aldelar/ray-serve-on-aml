import json
from fastapi import FastAPI
import ray
from ray import serve
# from ray.serve.deployment_graph import ClassNode
from ray.serve.handle import RayServeDeploymentHandle
from pydantic import BaseModel

# 1: Define a FastAPI app and wrap it in a deployment with a route handler.
app = FastAPI()

class NewName(BaseModel):
    new_name:str


@serve.deployment
class Workshop:
    def __init__(self, workshop_name : str = "Ray-On-Azure") -> None:
        # super().__init__()
        self.workshop_name = workshop_name

    def get_workshop_name(self) -> str:
        return str(self.workshop_name)

    def set_workshop_name(self, new_name) -> None:
        self.workshop_name = new_name

    def __str__(self) -> str:        
        return str(self.workshop_name)


@serve.deployment
@serve.ingress(app)
class FastAPIDeployment:
    def __init__(self, *workshops : RayServeDeploymentHandle) -> None:
        self.workshops = workshops
        # self.workshopList = []
        for workshop in workshops:
            # self.workshopList.append(workshop)
            print(workshop)

    # FastAPI will automatically parse the HTTP request for us.
    @app.get("/hello")
    def say_hello(self, name: str) -> str:
        return f"Hello {name}!"

    @app.get("/get_bind_nodes")
    def get_bind_nodes(self):
        nodes = {}
        i = 0
        for w in self.workshops:
            i = i + 1
            nodes[f"actor_{i}"] = i
            # nodes["name"] = str(ray.get(w.get_workshop_name.remote()))
            nodes[f"name_{i}"] = str(w)
        return json.dumps(nodes)

    @app.post("/set_workshop_name")
    async def set_workshop_name(self, new_name : NewName) -> str:
        nodes = {}
        i = 0
        for w in self.workshops:
            i = i + 1
            nodes[f"actor_{i}"] = i
            await w.set_workshop_name.remote(new_name.new_name)
            ref: ray.ObjectRef = await w.get_workshop_name.remote()
            nodes[f"name_{i}"] = await ref

        # for w in self.workshopList:
        #     print(w)
        #     # i = i + 1
        #     # nodes[f"actor_{i}"] = i
        #     # await w.set_workshop_name.remote(new_name.new_name)
        #     # nodes[f"name_{i}"] = await w.get_workshop_name.remote()

        return json.dumps(nodes)


workshop1 = Workshop.bind(workshop_name="1_wrkshp_1")
workshop2 = Workshop.bind(workshop_name="2_wrkshp_2")
workshop3 = Workshop.bind(workshop_name="3_wrkshp_3")


fastapideployment = FastAPIDeployment.bind(workshop1, workshop2, workshop3)

# 2: Deploy the deployment.
# serve.run()

# # 3: Query the deployment and print the result.
# print(requests.get("http://localhost:8000/hello", params={"name": "Theodore"}).json())
# # "Hello Theodore!"