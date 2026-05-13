from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def home():
    return {"message": "YouthPath API is running"}