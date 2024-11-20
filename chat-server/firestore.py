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

def load_org_info(org_uuid) -> str:
    doc = db.document(f"COMPANY/{org_uuid}/Data/ai_training_data")
    org_info = doc.get().get("trainingData")
    if org_info is None:
        print(f"warning: org '{org_uuid}' is 404", flush=True)
        return ""
    return org_info
