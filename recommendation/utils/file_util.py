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
    except Exception as e:
        logging.error("load failed: " + path)
        logging.error(e)
    return json_data
