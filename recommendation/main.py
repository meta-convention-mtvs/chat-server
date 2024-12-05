import asyncio
from concurrent.futures import ThreadPoolExecutor
from contextlib import asynccontextmanager
import threading
from fastapi import FastAPI
import uvicorn
import ssl
from schema.user import UserInfo
from schema.company import CompanyInsInfoForRecommendation
from service.recommendation import exec_recommendation
from service.company_data_handle import save_company_data
from config import log
import logging

# 인증서 관련 오류 방지
ssl._create_default_https_context = ssl._create_unverified_context

# client = FirebaseClient()
# @asynccontextmanager
# async def lifespan(app: FastAPI):
#     executor = run_listener_in_background()
#     try:
#         yield
#     finally:
#         cleanup_listener(executor)
# app = FastAPI(lifespan=lifespan)        

app = FastAPI()


@app.get("/")
async def hello():
    return {'result': 'hello'}


@app.post("/recommendation")
async def recommendation(userinfo: UserInfo):
    return {'result': exec_recommendation(userinfo)}


@app.post('/recommendation/{uuid}')
async def create_recommendation_data(uuid: str, companyinfo: CompanyInsInfoForRecommendation):    
    save_company_data(companyinfo.description, uuid, companyinfo)


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=3000, reload=True)
