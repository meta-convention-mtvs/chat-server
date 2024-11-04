from sentence_transformers import SentenceTransformer

class EmbeddingModel():
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(EmbeddingModel, cls).__new__(cls)
            cls._instance._initialize(*args, **kwargs)
        return cls._instance

    def _initialize(self, model_name="jinaai/jina-embeddings-v3", trust_remote_code=True):
        self.model = SentenceTransformer(model_name, trust_remote_code=trust_remote_code).cuda()

    def get_model(self):
        return self.model