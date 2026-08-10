import uvicorn


def run() -> None:
    uvicorn.run("reflection_ai.api:app", host="0.0.0.0", port=8000, reload=True)
