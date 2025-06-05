import json

def load_and_update_workflow(path: str, user_prompt: str, job_id: str):
    with open(path, "r") as f:
        raw = json.load(f)

    if "prompt" in raw:
        nodes = raw["prompt"]
    else:
        nodes = raw

    for key, node in nodes.items():
        ctype = node.get("class_type")
        if ctype == "CLIPTextEncode":
            if "inputs" in node and "text" in node["inputs"]:
                node["inputs"]["text"] = user_prompt

        if ctype == "SaveImage":
            if "inputs" in node and "filename_prefix" in node["inputs"]:
                node["inputs"]["filename_prefix"] = f"ComfyUI_{job_id}"

    # Keep the same wrapper (“prompt”) if it existed, and inject metadata
    raw["extra_data"] = {"job_id": job_id}
    return raw
