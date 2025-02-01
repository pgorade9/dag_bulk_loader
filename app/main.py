from fastapi import FastAPI
import uvicorn

from service.api import router

app = FastAPI()


@app.get("/")
def index():
    return "hello world"


app.include_router(router)

if __name__ == "__main__":
    uvicorn.run("app.main:app", port=8080, host="127.0.0.1")
