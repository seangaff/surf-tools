# 1. Import the library
from inference_sdk import InferenceHTTPClient

# 2. Connect to your workflow
client = InferenceHTTPClient(
    api_url="https://serverless.roboflow.com",
    api_key="6BeVnvYPVTQXnlAbglDt"
)

# 3. Run your workflow on an image
result = client.run_workflow(
    workspace_name="surf-0ekhl",
    workflow_id="sam-3",
    images={
        "image": "YOUR_IMAGE.jpg" # Path to your image file
    },
    parameters={
        "className": ["surfer"]
    },
    use_cache=True # Speeds up repeated requests
)

# 4. Get your results
print(result)
