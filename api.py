import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from agent.config_manager import load_config, save_config

app = FastAPI(title="SmileLine Dental Admin API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/config")
def get_config():
    try:
        return load_config()
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Config file not found")


@app.put("/api/config")
def update_config(config: dict):
    required_keys = {"system_prompt", "persona", "tools"}
    if not required_keys.issubset(config.keys()):
        raise HTTPException(
            status_code=422,
            detail=f"Config must contain keys: {required_keys}",
        )
    save_config(config)
    return {"status": "ok"}


if __name__ == "__main__":
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)
