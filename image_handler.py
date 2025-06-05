import requests
import time
import os

COMFYUI_URL = "http://127.0.0.1:8188"
OUTPUT_DIR = os.path.expanduser("~/ComfyImage/output")

def submit_workflow(workflow: dict):
    response = requests.post(f"{COMFYUI_URL}/prompt", json=workflow)
    response.raise_for_status()
    return response.json()  # contains "prompt_id", etc.

def wait_for_image(job_id: str, timeout=60):
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            for fname in os.listdir(OUTPUT_DIR):
                if job_id in fname and fname.endswith(".png"):
                    return os.path.join(OUTPUT_DIR, fname)
        except FileNotFoundError:
            pass
        time.sleep(1)
    raise TimeoutError("Image generation timed out.")
