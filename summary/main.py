import logging
from fastapi import FastAPI, HTTPException, status
import uvicorn
from schema.user import BuyerAIConversationSummaryRequest
from config import log
from service.summary import exec_summary


app = FastAPI()

@app.get("/")
async def hello():
    return {'result': 'summary'}

@app.post("/summary")
async def summary(userinfo:BuyerAIConversationSummaryRequest) -> dict:
    try:
        result = exec_summary(userinfo)
        if not result:
            raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="유저가 해당 기업의 AI직원과 대화한 기록을 찾을 수 없음",
        )
        return result 
    except Exception as e:
        logging.error(e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="요약 중 에러 발생",
        )
        

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=3000, reload=True)
