# Service component map

## Service Initiation

`dispatcher` from the `many_models_serving.py` will be initiated by the `ray_service.yaml` and prior to this the `many_models_serving.py` will be downloaded by the spec in `ray_service.yaml`.

The `dispatcher` will be instantiated and it creates a map of ClassNode(Represents an actor creation in a Ray task DAG) and `sharedmemory`.

The variable `dispatcher` binds with many `deployment#` classes.

```py
dispatcher = Dispatcher.bind(deployment1, deployment2, deployment3, deployment4, deployment5, deployment6, deployment7, deployment8, deployment9, deployment10, deploymentx, sharedmemory)
```

It instantiate deployment# which will hold a model per deployment instance.



## Service components
