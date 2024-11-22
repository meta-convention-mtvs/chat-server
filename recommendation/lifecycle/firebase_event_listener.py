import asyncio
import logging
from concurrent.futures import ThreadPoolExecutor
from model.firebase_client import FirebaseClient


client = FirebaseClient()

# 리스터 시작
def start_firebase_listener():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    client.listen_collection()
    
    try:
        loop.run_forever()
    except Exception as e:
        logging.error(f"Listener error: {e}")
    finally:
        loop.close()


# 리스너 실행을 관리
def run_listener_in_background():
    executor = ThreadPoolExecutor(max_workers=1)
    if not client._listener_active:
        future = executor.submit(start_firebase_listener)
    return executor

# 리스너 종료를 관리
def cleanup_listener(executor):
    executor.shutdown(wait=False)
    if hasattr(client, 'watch'):
        client.watch.unsubscribe()