import os

# 루트 디렉토리
ROOT_DIR = "/"

CONFIG_DIR = 'config'
CHATBOT_CONFIG = os.path.join(CONFIG_DIR, 'chatbot_config.json')

DATA_DIR = 'data'

# 로그 파일 저장 경로 설정
# ./logs
LOG_DIR = os.path.join(ROOT_DIR, 'logs')


# 디렉토리 생성
os.makedirs(DATA_DIR, mode=0o777, exist_ok=True)
os.makedirs(LOG_DIR, mode=0o777, exist_ok=True)