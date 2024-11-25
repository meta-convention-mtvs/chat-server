import firebase_admin
from firebase_admin import credentials, firestore
import logging
import threading
from service.company_data_handle import save_company_data

class FirebaseClient:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super().__new__(cls, *args, **kwargs)
            cls._instance._initialize()
        return cls._instance


    def _initialize(self):
        try:
            cred = credentials.Certificate("firebase-key.json")
            if not firebase_admin._apps:
                firebase_admin.initialize_app(cred)
            self.db = firestore.client()
        except:
            print("ERROR - Firebase를 연결하는데 문제 발생")
            logging.error("ERROR - Firebase를 연결하는데 문제 발생")
    
    
    def load_roots(self):
        return [collection.id for collection in self.db.collections()]


    def load_org_info(self, org_uuid) -> str:
        doc = self.db.document(f"COMPANY/{org_uuid}/Data/ai_training_data")
        org_info = doc.get().get("trainingData")
        if org_info is None:
            print(f"warning: org '{org_uuid}' is 404", flush=True)
            return ""
        return org_info
    
    
    def __init__(self):
        self._listener_active = False
        self.processed_documents = set()

    def listen_collection(self):
            if self._listener_active:
                logging.warning("Listener already active, skipping...")
                return

            self._listener_active = True
            initial_snapshot = True  # 초기 스냅샷 여부를 추적하는 플래그

            def on_snapshot(col_snapshot, changes, read_time):
                nonlocal initial_snapshot
                try:
                    logging.debug(f"Snapshot received at {read_time}")

                    if initial_snapshot:
                        # logging.info("Processing initial snapshot")
                        # for doc in col_snapshot:
                        #     self._process_document(doc)
                        initial_snapshot = False
                    else:
                        for change in changes:
                            if change.type.name == 'ADDED':
                                self._process_document(change.document)
                            elif change.type.name == 'MODIFIED':
                                logging.debug(f"Modified document: {change.document.id}")
                            elif change.type.name == 'REMOVED':
                                logging.debug(f"Removed document: {change.document.id}")

                except Exception as e:
                    logging.error(f"Error in snapshot listener: {e}")

            col_ref = self.db.collection("COMPANY")
            self.watch = col_ref.on_snapshot(on_snapshot)

            return self.watch

    def _process_document(self, doc):
        doc_id = doc.id
        if doc_id not in self.processed_documents:
            logging.debug(f"Processing document: {doc_id}")
            doc_data = doc.to_dict()
            if doc_data and 'Data' in doc_data:
                org_info = (doc_data.get('Data', {})
                            .get('ai_training_data', {})
                            .get('trainingData'))
                if org_info:
                    save_company_data(org_info, doc_id)
                    self.processed_documents.add(doc_id)
                    logging.debug(f"Successfully processed document: {doc_id}")