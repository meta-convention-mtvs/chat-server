
from pprint import pprint
from model.chatbot import ChatBotManager
from model.embedding import EmbeddingModel
from utils.file_util import save_to_json, load_json_data, append_to_json
from tqdm import tqdm
import torch
import numpy as np
import faiss
from model.chatbot import ChatBotManager
from config.path import CHATBOT_CONFIG, DATA_DIR


chatbot_manager = ChatBotManager(CHATBOT_CONFIG)
embedding_model = EmbeddingModel().get_model()
keyword_chatbot = chatbot_manager.get_chatbot('keyword_extraction')

'''
1. 기업 데이터를 수집. 예시: 3.unique_merged_data.json
2. 키워드로만 이뤄진 기업 데이터가 없을시 make_keywords 실행. 
3. 2의 아웃풋 값 기준으로 faiss 인덱스 생성
'''


def make_keywords(company:dict, keyword_file_path:str) -> dict: 
    inner_data = None
    company_data = keyword_chatbot.exec(f"{company['tags']} {company['company_mission']} {company['items']}에서 핵심 키워드를 추출해줘", None)
    inner_data = {} 
    inner_data['company_name'] = company['company_name']
    inner_data['keywords'] = company_data
    append_to_json(keyword_file_path, inner_data)
    return inner_data
    
  
# 기업 데이터에서 키워드 추출할 때 사용
def make_keywords_using_json_list(company_file_path:str, keyword_file_path:str) -> None: 
    companies = load_json_data(company_file_path)
    data = []
    for company in companies:
        inner_data = make_keywords(company, keyword_file_path)
        data.append(inner_data)
        pprint(inner_data)
    return data
    
    
# faiss 인덱스화
def make_faiss_index(company_with_keywords:dict, company_info:dict) -> None:    
    company_embedding = embedding_model.encode(
        company_with_keywords['keywords'],
        task='text-matching',
        convert_to_tensor=True  # GPU에서 PyTorch 텐서로 변환
    )
    
    # 코사인 유사도를 위해 벡터 정규화
    company_embedding = company_embedding.float()
    company_embedding = company_embedding / company_embedding.norm(dim=0, keepdim=True)
    company_embedding_list = company_embedding.tolist()

    embeddings = np.array([company_embedding_list]).astype('float32')
    loaded_index = faiss.read_index(f'{DATA_DIR}/company_cosign.index')
    loaded_index.add(embeddings)
    
    faiss.write_index(loaded_index, f'{DATA_DIR}/company_cosign.index')
    append_to_json(f'{DATA_DIR}/company_metadata.json', company_info)
    
    


# faiss 인덱스화 - 전체 다시 할 때
def make_faiss_index_using_json_list(company_keyword_path:str, whole_companyinfo_path:str) -> None:
    company_keywords = load_json_data(company_keyword_path)
    company_whole = load_json_data(whole_companyinfo_path)

    embeddings = []
    metadata = []
    for company in tqdm(company_keywords):
        company_embedding = embedding_model.encode(
            company['keywords'],
            task='text-matching',
            convert_to_tensor=True  # GPU에서 PyTorch 텐서로 변환
        )
        
        # 코사인 유사도를 위해 벡터 정규화
        company_embedding = company_embedding.float()
        company_embedding = company_embedding / company_embedding.norm(dim=0, keepdim=True)
        company_embedding_list = company_embedding.tolist()
        
        # cpu 사용시
        # company_embedding_cpu = company_embedding.cpu()
        # company_embedding_list = company_embedding_cpu.tolist()
        
        # gpu 사용시
        # company_embedding_list = company_embedding.tolist()
        
        embeddings.append(company_embedding_list)
        metadata.append(company_whole[company['company_name']])
    
    embeddings = np.array(embeddings).astype('float32')

    # Faiss 인덱스 생성 및 임베딩 추가
    dimension = embeddings.shape[1]

    index = faiss.IndexFlatIP(dimension)  # 내적을 사용하여 코사인 유사도 계산
    # index = faiss.IndexFlatL2(dimension) # 거리 기반

    index.add(embeddings)
    
    # 인덱스를 파일로 저장
    faiss.write_index(index, f'{DATA_DIR}/company_cosign.index')
    save_to_json(f'{DATA_DIR}/company_metadata.json', metadata)

# torch.cuda.empty_cache()
# make_keywords(f'{DATA_DIR}/refined_data_with_tags.json', f'{DATA_DIR}/4.company_keyword.json')
# make_faiss_index(f'{DATA_DIR}/4.company_keyword.json', f'{DATA_DIR}/company_metadata.json')