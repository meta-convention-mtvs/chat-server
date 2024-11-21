
from model.chatbot import ChatBotManager
from model.embedding import EmbeddingModel
from utils.file_util import load_json_data, get_json_from_str
from utils.data_management import make_keywords, make_faiss_index
from config.path import CHATBOT_CONFIG, CONFIG_DIR, DATA_DIR
from pprint import pprint
import json
import logging

chatbot_manager = ChatBotManager(CHATBOT_CONFIG)
embedding_model = EmbeddingModel().get_model()
data_refinement_bot = chatbot_manager.get_chatbot('data_refinement')
tag_maker_bot = chatbot_manager.get_chatbot('tag_maker')

tags = {'3D Printing',
 '5G Technologies',
 'AR/VR/XR',
 'Accessibility',
 'Accessories',
 'AgTech',
 'Artificial Intelligence',
 'Audio',
 'Cloud Computing',
 'Construction Tech',
 'Content and EntertaInment',
 'Cybersecurity',
 'Defense',
 'Digital Health',
 'Drones',
 'Education Tech',
 'Energy Transition',
 'Energy/Power',
 'Enterprise',
 'Fashion Tech',
 'Fintech',
 'Fitness',
 'Food Tech',
 'Gaming and Esports',
 'Home Entertainment and Office Hardware',
 'Imaging',
 'Innovation',
 'Investing',
 'IoT/Sensors',
 'Lifestyle',
 'Marketing and Advertising',
 'Metaverse',
 'NFT',
 'Retail/E-Commerce',
 'Robotics',
 'Smart Cities',
 'Smart Home and Appliances',
 'Sourcing and Manufacturing',
 'Space Tech',
 'Sports',
 'Startups',
 'Streaming',
 'Style',
 'Supply and Logistics',
 'Sustainability',
 'Technology',
 'Travel and Tourism',
 'Vehicle Tech and Advanced Mobility',
 'Video'}

def make_company_data_for_recommendation(data:str) -> None:
    loaded_data = load_json_data(f'{CONFIG_DIR}/company_data_sample.json')
    company_data = data_refinement_bot.exec(f"input1: {data} // input2: {loaded_data}", None)
    company_data = get_json_from_str(company_data)
    if 'tags' in company_data:
        result = tag_maker_bot.exec(f"input1: {company_data} // input2: {tags}", None)
        print(result)
        company_data['tags'] = result.split(', ')
    else:
        logging.error(f'invalid extraction with : {data}')
        return None
    return company_data


def save_company_data(data:str) -> None:
    
    logging.debug(data)
    # whole company_data
    company_data = make_company_data_for_recommendation(data)
    
    # company_data with keyword
    company_keywords = make_keywords(company_data, f'{DATA_DIR}/4.company_keyword.json')
    
    # add index
    make_faiss_index(company_keywords, company_data)