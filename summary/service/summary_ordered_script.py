from itertools import zip_longest
from schema.user import BuyerAIConversationSummaryRequest
from service import iso_639_lang
from utils.file_util import read_text
from model.chatbot import ChatBotManager
from config.path import CHATBOT_CONFIG, AI_CONVERSATION_DIR
import logging
from pprint import pprint
from glob import glob
from typing import List, Dict, Tuple, Optional

chatbot_manager = ChatBotManager(CHATBOT_CONFIG)
summary_chatbot = chatbot_manager.get_chatbot('summary')

def parse_line(line: str) -> Optional[Dict[str, str]]:
    """대화 로그의 각 라인을 파싱하여 발화자와 내용 추출"""
    if '>> (audio) ' in line:  # 고객 메시지
        content = line[line.find('(audio) ') + 8:]
        return {'sender': 'customer', 'content': content}
    elif '<< (audio) ' in line:  # AI 메시지
        content = line[line.find('(audio) ') + 8:]
        return {'sender': 'ai', 'content': content}
    return None

def merge_consecutive_messages(messages: List[Dict[str, str]]) -> List[Dict[str, List[str]]]:
    """연속된 동일 발화자의 메시지를 하나로 병합"""
    merged = {'ai':[], 'customer':[]}
    current_group = None
    
    for msg in messages:
        if current_group is None or current_group['sender'] != msg['sender']:
            merged[msg['sender']].append(msg['content'])
            current_group = {
                'sender': msg['sender'],
                'content': [msg['content']]
            }
        else:
            merged[msg['sender']].append(msg['content'])
    
    pprint('-------------------------------')
    print(merged)
    pprint('--------------------------------')
    return merged


def refine_script(text: List[str]) -> Tuple[Dict[str, List[str]], str]:
    """대화 내용을 정제하여 고객-AI 쌍과 전체 스크립트 생성"""
    # 1단계: 각 라인을 파싱하여 발화자와 내용 추출
    messages = []
    for line in text:
        if parsed := parse_line(line):
            messages.append(parsed)
    
    if not messages:
        return {'customer': [], 'AI': []}, ''
    
    # 2단계: 연속된 메시지 병합
    merged = merge_consecutive_messages(messages)
    
    ai_messages = merged.get('ai', [])
    customer_messages = merged.get('customer', [])

    # 전체 스크립트 생성
    script_lines = []
    for customer_message, ai_message in zip_longest(customer_messages, ai_messages, fillvalue=None):
        if customer_message is not None:
            script_lines.append(f"customer: {customer_message}")
        if ai_message is not None:
            script_lines.append(f"AI: {ai_message}")
    

    return merged, '\n'.join(script_lines)

def find_conversation_file(userinfo: BuyerAIConversationSummaryRequest) -> Optional[str]:
    """사용자의 가장 최근 대화 파일 찾기"""
    for file_path in sorted(glob(f"{AI_CONVERSATION_DIR}/*"), reverse=True):
        with open(file_path, "r") as file:
            file.readline()  # skip first line
            try:
                user_info = file.readline().split()
                if (user_info[3].strip() == userinfo.user_id and 
                    user_info[5].strip() == userinfo.org_id):
                    return file_path
            except IndexError as e:
                logging.debug(f"Error processing {file_path}: {e}")
    return None

def exec_summary(userinfo: BuyerAIConversationSummaryRequest) -> Optional[Dict[str, str]]:
    """대화 내용 요약 실행"""
    file_path = find_conversation_file(userinfo)
    if not file_path:
        return None

    print(file_path)
    text = read_text(file_path)
    conversation, full_script = refine_script(text.split('\n'))
    
    if not conversation['customer']:
        summary = '유효한 대화 내용이 없습니다'
    else:
        lang = iso_639_lang.to_full_lang(userinfo.lang)
        prompt = (f'You need to wrap up sentences in {lang}. '
                 f'do your work with followed senetences {conversation["customer"]}')
        summary = summary_chatbot.exec(prompt, None)
    
    result = {'summary': summary, 'full_script': full_script}
    pprint(result)
    logging.debug(result)
    return result