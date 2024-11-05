from fastapi import HTTPException
import numpy as np
from deep_translator import GoogleTranslator
from tqdm import tqdm
import faiss
import logging
import concurrent.futures

from schema.user import UserInfo
from utils.file_util import load_json_data
from model.chatbot import ChatBotManager
from model.embedding import EmbeddingModel
from config.path import CHATBOT_CONFIG, DATA_DIR


chatbot_manager = ChatBotManager(CHATBOT_CONFIG)
embedding_model = EmbeddingModel().get_model()
keyword_chatbot = chatbot_manager.get_chatbot('keyword_extraction')
recommend_reaason_chatbot = chatbot_manager.get_chatbot('recommendation_reason')

# 추천 시스템
def recommend(user:str, recommend_num:int=10) -> list[dict]:
    try:
        user_embedding =  embedding_model.encode([user], task='text-matching')
        # 저장된 인덱스를 파일에서 로드
        loaded_index = faiss.read_index(f'{DATA_DIR}/company.index')
        loaded_metadata = load_json_data(f'{DATA_DIR}/company_metadata.json')
        _, indices = loaded_index.search(np.array(user_embedding).reshape(1, -1), recommend_num)
        recommendations = [loaded_metadata[indices[0][i]] for i in range(recommend_num)]
        return recommendations
    except Exception as e:
        logging.error(e)    


# 전부 없음인 경우 추천하지 않음
def check_userinfo(userinfo:UserInfo) -> bool:
    if '-' in userinfo.industry_type and '-' in userinfo.selected_interests and '-' == userinfo.situation_description:
        return False
    return True
    

def get_user_keywords(userinfo:UserInfo) -> str:
    try: 
        user_data = []
        if traslated_value:= GoogleTranslator(source='auto', target='en').translate(str(userinfo)):
            user_data.append(traslated_value)   
        user = keyword_chatbot.exec(f'{userinfo}', None)
        return user
    except Exception as e:
        logging.error(e)


def add_reason_of_recommendation(userinfo:UserInfo, recommandation_data:list[dict]) -> str:
    try:
        for company in recommandation_data:
            answer = recommend_reaason_chatbot.exec(f'유저 정보: {userinfo}, 기업 정보: {company}', None)
            company['reason'] = answer
        return recommandation_data
    except Exception as e:
        logging.error(e)


def add_reason_of_recommendation_parallel(userinfo: UserInfo, recommendation_data: list[dict]) -> list[dict]:
    def process_company(company):
        try:
            answer = recommend_reaason_chatbot.exec(f'유저 정보: {userinfo}, 기업 정보: {company}', None)
            company['reason'] = answer
            return company
        except Exception as e:
            print(f"Error processing company: {e}")
            return company

    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        return list(executor.map(process_company, recommendation_data))


def exec_recommendation(userinfo:UserInfo) -> str:
    if not check_userinfo(userinfo):
        return '유저 정보가 충분하지 않습니다'

    user = get_user_keywords(userinfo)
    recommendations = recommend(user)
    # result = add_reason_of_recommendation(userinfo, recommendations)
    result = add_reason_of_recommendation_parallel(userinfo, recommendations)

    return result

