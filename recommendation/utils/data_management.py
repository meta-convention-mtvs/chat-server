
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

# 기업 데이터에서 키워드 추출할 때 사용
def make_keywords(company_file_path:str, keyword_file_path:str) -> None: 
    companies = load_json_data(company_file_path)
    data = []
    for company in companies:
        company_data = keyword_chatbot.exec(f"{company['tags']} {company['company_mission']} {company['items']}에서 핵심 키워드를 추출해줘", None)
        inner_data = {} 
        inner_data['company_name'] = company['company_name']
        inner_data['keywords'] = company_data
        data.append(inner_data)
        pprint(inner_data)

    append_to_json(keyword_file_path, data)
    
    
# 미리 기업 데이터 임베딩 해놓을 때 사용 - json형식. faiss로 변경 후 안 쓰임.
def make_embeddings_to_json(company_keyword_path:str, embeding_path:str) -> None:
    companies = load_json_data(company_keyword_path)
    company_embeddings = {}
    for company in tqdm(companies):
        company_embedding = embedding_model.encode(company['keywords'], task='text-matching')
        company_embeddings[company['company_name']] = company_embedding.tolist()
    save_to_json(embeding_path, company_embeddings)


# faiss 인덱스화
def make_faiss_index(company_keyword_path:str, whole_companyinfo_path:str) -> None:
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
        
        # cpu 사용시
        # company_embedding_cpu = company_embedding.cpu()
        # company_embedding_list = company_embedding_cpu.tolist()
        
        # gpu 사용시
        company_embedding_list = company_embedding.tolist()
        
        embeddings.append(company_embedding_list)
        metadata.append(company_whole[company['company_name']])
    
    embeddings = np.array(embeddings).astype('float32')

    # Faiss 인덱스 생성 및 임베딩 추가
    dimension = embeddings.shape[1]
    index = faiss.IndexFlatL2(dimension)
    index.add(embeddings)
    
    # 인덱스를 파일로 저장
    faiss.write_index(index, f'{DATA_DIR}/company2.index')
    save_to_json(f'{DATA_DIR}/company_metadata2.json', metadata)

# torch.cuda.empty_cache()
# make_keywords(f'{DATA_DIR}/3.unique_merged_data.json', f'{DATA_DIR}/4.company_keyword.json')
# make_faiss_index(f'{DATA_DIR}/4.company_keyword.json', f'{DATA_DIR}/5.unique_merged_data_with_key.json')