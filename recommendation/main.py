import asyncio
from concurrent.futures import ThreadPoolExecutor
from contextlib import asynccontextmanager
import threading
from fastapi import FastAPI
import uvicorn
import ssl
from config.path import DATA_DIR
from utils.file_util import load_json_data
from utils.data_management import make_faiss_index, make_keywords, make_keywords_using_json_list, make_faiss_index_using_json_list
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


@app.post('/data')
async def data():
    # keyword
    data = make_keywords_using_json_list(f'{DATA_DIR}/company_metadata.json', f'{DATA_DIR}/4.company_keyword.json')
    
    # make faiss index - full
    make_faiss_index_using_json_list(f'{DATA_DIR}/4.company_keyword.json')
    
    # add faiss index - part
    # whole_company_data = load_json_data(f'{DATA_DIR}/company_metadata.json')
    # for index, cur_data in enumerate(data):
    #     make_faiss_index(cur_data, whole_company_data[index])
    #     print(cur_data)
   
    
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=3000, reload=True)
