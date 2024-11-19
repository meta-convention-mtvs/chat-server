from fastapi import FastAPI
import uvicorn
import ssl
from schema.user import UserInfo
from service.recommendation import exec_recommendation
from service.company_data_handle import save_company_data
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

@app.get('/test')
async def test():
    test_data = """Boston Dynamics는 오늘날과 미래의 가장 어려운 자동화 과제를 해결하기 위해 실용적인 로봇 솔루션을 개발하는 데 주력하고 있습니다. 이 회사는 다양한 환경을 탐색하고 데이터를 수집하며 사람들의 안전을 지키는 기민하고 이동성이 뛰어난 로봇인 Spot을 제공합니다. 또한, Stretch는 케이스 핸들링과 트레일러 하역 작업을 간소화하도록 설계된 로봇으로, 쉽게 배치할 수 있고 유연하게 사용할 수 있습니다. 마지막으로, Atlas는 높은 이동성, 유연성, 지능을 추구하는 Boston Dynamics의 차세대 로봇을 대표합니다. Boston Dynamics는 이러한 혁신적인 제품들을 통해 로봇 공학의 미래를 이끌어가고 있습니다.
    """
    save_company_data(test_data)
    


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=3000, reload=True)
