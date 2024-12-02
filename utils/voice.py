import os
from openai import OpenAI
from tqdm import tqdm

client = OpenAI()
os.makedirs("audio", exist_ok=True)

case1 = [
    "😄😄😄😄😄😄😄😄 안녕하세용! 언어의 장벽 없이 전 세계 기업 부스를 탐험하고, 글로벌 비즈니스 미팅을 지원하는 메타컨벤션에 오신 걸 환영해요! 원하는 부스를 관람하실 수 있도록🎶 제가 부스를 추천해드릴게요.😊😊😊 관심사나 원하는 정보를 입력해보세요!!!",
    "😄😄😄😄😄😄😄😄 Hello and welcome to Meta Convention, where you can effortlessly explore global corporate booths without language barriers and connect for business meetings! To help you find the right booths, I’ll recommend options based on your interests or needs. Just let me know what you're looking for, and I'll guide you!",
    "😄😄😄😄😄😄😄😄 你好，欢迎来到META CONVENTION！ 在这里，你可以轻松探索全球企业展位，参加商务会议。 请告诉我你感兴趣的信息，我会为你推荐合适的展位！",
]

case2 = [
    "😄😄😄😄😄😄😄😄 안녕하세요, 당신의 맞춤형 비서입니다. 이제부터 하시는 모든 말씀을 제가 통역해드릴게요!",
    "😄😄😄😄😄😄😄😄 Hello! I’m your personal assistant. From now on, I’ll translate everything you say for you!",
    "😄😄😄😄😄😄😄😄 你好!我是你的助理。从现在开始你说的每句话我都会翻译给你!",
]

lang = ["ko", "en", "zh"]

def to_audio_file(text, file_name):
    response = client.audio.speech.create(
        model="tts-1-hd",
        voice="ballad",
        input=text,
    )
    response.stream_to_file(file_name)


# for item in tqdm(list(zip(case1, lang))):
#     to_audio_file(item[0], f"rec_{item[1]}.mp3")

# for item in tqdm(list(zip(case2, lang))):
#     to_audio_file(item[0], f"trans_{item[1]}.mp3")

    
to_audio_file(case1[0], f"asdf.mp3")
