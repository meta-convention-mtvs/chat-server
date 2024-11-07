from pydantic import BaseModel

class BuyerAIConversationSummaryRequest(BaseModel):
    user_id: str
    org_id: str
    lang: str