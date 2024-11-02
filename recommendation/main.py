from fastapi import FastAPI
import uvicorn
from schema.user import UserInfo
from service.recommendation import exec_recommendation


app = FastAPI()

@app.get("/")
async def hello():
    return {'result': 'hello'}

@app.post("/test")
async def test(userinfo:UserInfo):
    return {'result': exec_recommendation(userinfo)}


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=3000, reload=True)
