from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from service.api import router

app = FastAPI()
# CORS configuration
origins = [
    "http://localhost:4200",
    "http://localhost:4201",  # Allow Angular app running on localhost:4200
    # Add other origins as needed
    # Note that for this list you need to specify localhost and 127.0.0.1 separately
]

# Add CORS middleware to allow requests from the specified origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # List of allowed origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all HTTP methods (GET, POST, etc.)
    allow_headers=["*"],  # Allows all headers
)

@app.get("/")
def index():
    return "hello world"


app.include_router(router)

if __name__ == "__main__":
    uvicorn.run("app.main:app", port=8081, host="127.0.0.1")
