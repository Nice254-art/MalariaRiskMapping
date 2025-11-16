import pickle
import sklearn
print(sklearn.__version__)  # Check current version

# Re-save the model
with open('malaria_model_expanded.pkl', 'wb') as f:
    pickle.dump(malaria_model_expanded.pkl, f)