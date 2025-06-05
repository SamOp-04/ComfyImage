from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
from pydantic import BaseModel
import uuid, json, os, time, requests, asyncio, random

app = FastAPI()

from fastapi.middleware.cors import CORSMiddleware

origins = ["http://localhost:3000"]  # Add other origins if necessary
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # Origins allowed to access the server
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods
    allow_headers=["*"],  # Allow all headers
    expose_headers=["Content-Disposition"],  # Expose this header for file downloads
)


COMFYUI_URL = "http://127.0.0.1:8188"
OUTPUT_DIR = r"C:\Users\samas\ComfyUI_windows_portable\ComfyUI\output"

class PromptInput(BaseModel):
    prompt: str
    workflow: str = "anime"

def load_and_update_workflow(path: str, user_prompt: str, job_id: str):
    with open(path, "r") as f:
        raw = json.load(f)

    if "prompt" not in raw:
        raw = {"prompt": raw}

    nodes = raw["prompt"]

    for nid, node in nodes.items():
        if node.get("class_type") == "CLIPTextEncode":
            node["inputs"]["text"] = user_prompt

    for nid, node in nodes.items():
        if node.get("class_type") == "SaveImage":
            node["inputs"]["filename_prefix"] = f"ComfyUI_{job_id}"

    for nid, node in nodes.items():
        if node.get("class_type") == "KSampler":
            node["inputs"]["seed"] = random.randint(0, 2**31 - 1)

    raw["extra_data"] = {"job_id": job_id}
    return raw

def submit_workflow(workflow: dict):
    r = requests.post(f"{COMFYUI_URL}/prompt", json=workflow)
    r.raise_for_status()
    return r.json()

def wait_for_image(job_id: str, timeout=60):
    start = time.time()
    while time.time() - start < timeout:
        try:
            for fname in os.listdir(OUTPUT_DIR):
                if job_id in fname and fname.lower().endswith(".png"):
                    return os.path.join(OUTPUT_DIR, fname)
        except FileNotFoundError:
            pass
        time.sleep(1)
    raise TimeoutError("Image generation timed out.")

@app.post("/generate")
async def generate_image(data: PromptInput):
    job_id = str(uuid.uuid4())
    try:
        workflow_map = {
            "real": "workflows/basic.json",
            "anime": "workflows/basic_anime.json",
        }
        workflow_path = workflow_map.get(data.workflow, "workflows/basic_anime.json")
        workflow = load_and_update_workflow(workflow_path, data.prompt, job_id)
        resp = submit_workflow(workflow)
        prompt_id = resp.get("prompt_id")
        return JSONResponse({"job_id": job_id, "prompt_id": prompt_id})
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

@app.post("/generate-upscale")
async def generate_upscale(
    workflow: str = Form(...),
    file: UploadFile = File(...),
):
    job_id = str(uuid.uuid4())
    upload_dir = "uploads"
    os.makedirs(upload_dir, exist_ok=True)
    file_path = os.path.join(upload_dir, f"{job_id}_{file.filename}")
    with open(file_path, "wb") as f:
        f.write(await file.read())
    try:
        workflow_path = "workflows/upscale.json"
        workflow_data = load_and_update_workflow(workflow_path, "", job_id)
        nodes = workflow_data.get("prompt", {})
        for nid, node in nodes.items():
            if node.get("class_type") == "ImageLoader":
                node["inputs"]["filename"] = file_path
        resp = submit_workflow(workflow_data)
        prompt_id = resp.get("prompt_id")
        return JSONResponse({"job_id": job_id, "prompt_id": prompt_id})
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

# ... your existing endpoints for /history, /image, /stream ...

@app.get("/history/{prompt_id}")
async def get_history(prompt_id: str):
    """
    Proxy to ComfyUI's /history/<prompt_id> so the frontend can poll real progress.
    """
    try:
        r = requests.get(f"{COMFYUI_URL}/history/{prompt_id}")
        r.raise_for_status()
        return JSONResponse(r.json())
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

from fastapi import Request

@app.api_route("/image/{job_id}", methods=["GET", "HEAD"])
async def serve_image(job_id: str, request: Request):
    """
    Serve the generated image file for the given job_id. Supports GET and HEAD requests.
    """
    try:
        if request.method == "HEAD":
            # If the method is HEAD, just check if the file exists without returning the content
            image_path = await asyncio.get_event_loop().run_in_executor(None, wait_for_image, job_id)
            # Return an empty response with headers for metadata
            return JSONResponse(content=None, headers={"Access-Control-Allow-Origin": "http://localhost:3000"})

        # If the method is GET, return the actual image
        image_path = await asyncio.get_event_loop().run_in_executor(None, wait_for_image, job_id)
        return FileResponse(
            image_path,
            headers={"Access-Control-Allow-Origin": "http://localhost:3000"}
        )
    except TimeoutError:
        raise HTTPException(status_code=504, detail="Image generation timed out.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/stream/{prompt_id}")
async def stream_progress(prompt_id: str):
    """
    Example SSE endpoint that polls ComfyUI’s history and pushes real progress
    back to the client. The client connects with new EventSource(...).
    """
    async def event_generator():
        while True:
            try:
                r = requests.get(f"{COMFYUI_URL}/history/{prompt_id}")
                r.raise_for_status()
                hist = r.json().get(prompt_id, {})
                status = hist.get("status", {})
                # e.g. status = {"status_str": "success", "completed": true, ...}

                if status.get("completed"):
                    # final message
                    yield f"data: DONE\n\n"
                    break
                else:
                    # you can inspect `status.get("messages")`, count nodes, etc., 
                    # and emit a rough percentage:
                    msgs = status.get("messages", [])
                    # Here we just send the raw status_str
                    yield f"data: {status.get('status_str')}\n\n"
                await asyncio.sleep(1)
            except Exception:
                yield f"data: ERROR fetching history\n\n"
                break

    return StreamingResponse(event_generator(), media_type="text/event-stream")
