from fastapi import FastAPI
import uvicorn
import ssl
from schema.user import UserInfo
from service.recommendation import exec_recommendation
from config import log


app = FastAPI()

# 인증서 관련 오류 방지
ssl._create_default_https_context = ssl._create_unverified_context

@app.get("/")
async def hello():
    return {'result': 'hello'}

@app.post("/recommendation")
async def recommendation(userinfo:UserInfo):
    return {'result': exec_recommendation(userinfo)}


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=3000, reload=True)
