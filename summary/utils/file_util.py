import json
from typing import Any
import logging
import os

def save_to_json(path:str, data:Any, strategy:str='w') -> None:
    try:
        with open(path, strategy, encoding='utf-8') as file:
            json.dump(data, file, ensure_ascii=False, indent=4)
        logging.info("save to: " + path)
    except Exception as e:
        logging.error("save failed: " + path)
        logging.error(e)
        
        
def append_to_json(path:str, data:Any) -> None:    
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as file:
            try:
                existing_data = json.load(file)
            except json.JSONDecodeError:
                existing_data = []
    else:
        existing_data = []
    
    existing_data.append(data)
    save_to_json(path, existing_data)
        

def load_json_data(path:str) -> Any:
    try:
        with open(path, "r", encoding="utf-8") as file:
            json_data = json.load(file)
            return json_data
    except Exception as e:
        logging.error("load failed: " + path)
        logging.error(e)



def read_text(path:str) -> str:
    try:
        with open(path, "r", encoding="utf-8") as file:
            text_data = file.read()
        return text_data
    except Exception as e:
        logging.error("file read failed: " + path)
        logging.error(e)
        
        
def get_json_from_str(data:str) -> dict:
    '''
    ```json
    ``` 형태에서 json 뽑아내기
    '''
    json_start = data.find('{') 
    json_end = data.rfind('}') + 1 
    try:
        return json.loads(data[json_start:json_end])
    except Exception as e:
        logging.error(e)
        return None


    