# customize the model_hanlder for your implementation, only 2 methods are required
import pickle

# required method: input is a serialized model
def load_model(serialized_model):
	# implement any custom logic to load model
	return pickle.loads(serialized_model)

# required method: input is model and data for inference
def predict(model, data):
	# implement any custom logic to predict
	return model.predict(data)