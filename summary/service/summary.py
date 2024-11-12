from schema.user import BuyerAIConversationSummaryRequest
from service import iso_639_lang
from utils.file_util import read_text
from model.chatbot import ChatBotManager
from config.path import CHATBOT_CONFIG, AI_CONVERSATION_DIR
import logging
from pprint import pprint
from glob import glob
import os

chatbot_manager = ChatBotManager(CHATBOT_CONFIG)
summary_chatbot = chatbot_manager.get_chatbot('summary')

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

def exec_summary(userinfo:'BuyerAIConversationSummaryRequest') -> dict:
    search_file = None
    for file_path in sorted(glob(f"{AI_CONVERSATION_DIR}/*"), reverse=True):
        with open(file_path, "r") as file:
            file.readline()  # skip
            try:
                user_info_line = file.readline()
                splited = user_info_line.split(" ") # date time *** user_id lang_code org_id
                user_id = splited[3].strip()
                lang_code = splited[4].strip()
                org_id = splited[5].strip()
                if (user_id == userinfo.user_id and org_id == userinfo.org_id) == False:
                    continue
                search_file = file_path
                break
            except IndexError as e:
                logging.error('invalid log: ' + e)
                os.remove(file_path)
                continue
    if search_file == None:
        return None
    print(search_file)
    text = read_text(search_file)
    lang = iso_639_lang.to_full_lang(userinfo.lang)
    splitted_script, full_script = refine_script(text.split('\n'))
    
    summary = summary_chatbot.exec(f'You need to wrap up sentences in {lang}. do your work with followed senetences {splitted_script['customer']}', None)
    data = {'summary': summary, 'full_script': full_script}
    pprint(data)
    logging.debug(data)
    return data
