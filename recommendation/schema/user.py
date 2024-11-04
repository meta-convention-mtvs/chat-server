from pydantic import BaseModel

class UserInfo(BaseModel):
    industry_type: list[str]
    selected_interests: list[str]
    situation_description: str
    language: str