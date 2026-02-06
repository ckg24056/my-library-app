from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "Docker環境が立ち上がりました！"}