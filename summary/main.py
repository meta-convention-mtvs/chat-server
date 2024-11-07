from fastapi import FastAPI
import uvicorn
from schema.user import UserInfo
from config import log
from service.summary import exec_summary


app = FastAPI()

@app.get("/")
async def hello():
    return {'result': 'summary'}

@app.post("/summary")
async def summary(userinfo:'UserInfo') -> dict:
    return exec_summary(None)


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=3000, reload=True)
