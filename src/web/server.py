import os
import json
import asyncio
import logging
import uvicorn
from typing import List, Dict, Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sse_starlette.sse import EventSourceResponse

from config import CONFIG
from src.web.log_handler import log_queue
from src.stats import load_stats, get_today_date_str

app = FastAPI(title="RocoBot Management API")

# 启用 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

shared_status = None 

@app.get("/api/ping")
async def ping():
    return {"status": "pong"}

@app.get("/api/config")
async def get_config():
    data = CONFIG.to_dict()
    if shared_status is not None:
        data["is_running"] = shared_status.get("is_running", False)
        data["running_mode"] = shared_status.get("running_mode", "smart")
    return data

@app.post("/api/config")
async def update_config(data: Dict[str, Any]):
    new_settings = data.get("settings", {})
    for key, value in new_settings.items():
        if hasattr(CONFIG, key):
            setattr(CONFIG, key, value)
        if shared_status is not None and key in ["is_running", "running_mode"]:
            shared_status[key] = value
            
    await asyncio.to_thread(CONFIG.save)
    return await get_config()

@app.get("/api/stats")
async def get_stats():
    stats = await asyncio.to_thread(load_stats)
    today = get_today_date_str()
    return {
        "today": stats.get(today, 0),
        "total": sum(stats.values()) if stats else 0
    }

@app.delete("/api/stats")
async def reset_stats():
    from src.stats import clear_stats
    await asyncio.to_thread(clear_stats)
    return {"status": "success"}

@app.get("/api/sequences")
async def list_sequences():
    if not os.path.exists(CONFIG.sequence_dir):
        return {"active": CONFIG.active_sequence, "sequences": []}
    files = [f for f in os.listdir(CONFIG.sequence_dir) if f.endswith(".json")]
    return {"active": CONFIG.active_sequence, "sequences": files}

@app.get("/api/sequences/{name}")
async def get_sequence(name: str):
    path = os.path.join(CONFIG.sequence_dir, name)
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="Sequence not found")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

@app.post("/api/sequences/{name}")
async def save_sequence(name: str, data: Any):
    path = os.path.join(CONFIG.sequence_dir, name)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    return {"status": "success"}

@app.delete("/api/sequences/{name}")
async def delete_sequence(name: str):
    path = os.path.join(CONFIG.sequence_dir, name)
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="Sequence not found")
    
    # 至少保留一个脚本的逻辑建议在前端处理，但后端也做简单防御
    files = [f for f in os.listdir(CONFIG.sequence_dir) if f.endswith(".json")]
    if len(files) <= 1:
        raise HTTPException(status_code=400, detail="Cannot delete the last remaining sequence")
        
    os.remove(path)
    return {"status": "success"}

@app.get("/api/logs")
async def stream_logs(request: Request):
    async def log_generator():
        while True:
            if await request.is_disconnected():
                break
            try:
                log = await asyncio.to_thread(log_queue.get, timeout=1.0)
                yield f"data: {log}\n\n"
            except:
                continue
    return EventSourceResponse(log_generator())

# 挂载静态文件 - 指向根目录下的 frontend/dist
dist_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../frontend/dist"))
if os.path.exists(dist_path):
    app.mount("/", StaticFiles(directory=dist_path, html=True), name="static")
else:
    logging.warning(f"Frontend dist path not found: {dist_path}")

def run_server(status_dict=None):
    global shared_status
    shared_status = status_dict
    uvicorn.run(app, host="0.0.0.0", port=CONFIG.web_port, log_level="info", access_log=False)
