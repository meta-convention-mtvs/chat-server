from schema.user import UserInfo
from utils.file_util import read_text
from model.chatbot import ChatBotManager
from config.path import CHATBOT_CONFIG, AI_CONVERSATION_DIR
from transformers import pipeline
from deep_translator import GoogleTranslator
import logging

chatbot_manager = ChatBotManager(CHATBOT_CONFIG)
summary_chatbot = chatbot_manager.get_chatbot('summary')

# 요약시스템
# def summary(user:str,) -> list[dict]:
#     answer = summary_chatbot.exec(None, None)


def refine_script(text:list[str]) -> dict:
    script_start_mapper = {'>> (text) ': 'customer', '>> (audio) ': 'customer', '<< (audio) ':'AI'}
    data = {'customer':[], 'AI':[]}
    appended_data = []
    for cur_script in text:
        for start_keyword in script_start_mapper.keys():
            if (start_index:=cur_script.find(start_keyword)) > 0:
                start_index += len(start_keyword)
                cur_teller = script_start_mapper[start_keyword]
                if cur_teller== 'customer':
                    script = cur_script[start_index:cur_script.find('😄')]
                    data['customer'].append(script)
                else:
                    script = cur_script[start_index:]
                    data['AI'].append(script)
                appended_data.append(f'{cur_teller}: {script}')
    return data, '\n'.join(appended_data)

def exec_summary(userinfo:UserInfo) -> dict:
    # 읽기 -> 사용자 로그
    # 어떻게 읽을 거지? 
    # 1. 사용자 내용 요약 
    # 2. (전체 내용) 사용자의 질의와 답변
    text = read_text(f'{AI_CONVERSATION_DIR}/20241106_113625_c84d2126-2ccf-4383-8866-aada93193029.txt')
    splitted_script, full_script = refine_script(text.split('\n'))

    summary = summary_chatbot.exec(splitted_script['customer'], None)
    print(summary)
    print(full_script)
    return {'summary': summary, 'full_script': full_script}

