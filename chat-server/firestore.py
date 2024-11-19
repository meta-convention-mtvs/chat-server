import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore

db = None

async def load_firestore(app):
    global db
    try:
        cred = credentials.Certificate("firebase-key.json")
        firebase_admin.initialize_app(cred)
        db = firestore.client()
    except:
        print("ERROR - Firebase를 연결하는데 문제 발생")
    yield
    db.close()

def load_roots():
    return [collection.id for collection in db.collections()]
