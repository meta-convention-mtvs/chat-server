import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore

from google.cloud.firestore_v1.document import DocumentReference
from google.cloud.firestore_v1.collection import CollectionReference

cred = credentials.Certificate("firebase-key.json")
firebase_admin.initialize_app(cred)

db = firestore.client()
def print_collections(collections: list[CollectionReference], level=0):
    for collection in collections:
        print(f"{' ' * level * 2}{collection.id}")
        ref: list[DocumentReference] = collection.list_documents()
        for document in ref:
            print(f"{' ' * (level * 2)}{collection.id}: {document.id}")
            print_collections(document.collections(), level + 1)
# print_collections(db.collections())
data = db.document("COMPANY_Example/998cdb3f-0959-44b5-aa27-5ecbdbcc316e/Data/ai_training_data")
print(data.get().get("trainingData"))
