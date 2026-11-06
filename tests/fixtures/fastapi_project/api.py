from fastapi import FastAPI

app = FastAPI()


@app.get("/health")
def health():
    return {"ok": True}


@app.post(path="/users")
def create_user():
    return {"id": 1}


@app.api_route("/items/{item_id}", methods=["GET", "DELETE"])
def item(item_id: int):
    return {"id": item_id}


@app.get("/internal", include_in_schema=False)
def internal():
    return {}


@app.get(dynamic_path)
def dynamic():
    return {}


@app.not_a_route("/ignored")
def ignored():
    return {}


raise RuntimeError("the scanner must not execute project code")
