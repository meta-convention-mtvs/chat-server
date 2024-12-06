from pydantic import BaseModel

class CompanyWithKeyword(BaseModel):
    company_name:str
    keywords:str
    
class CompanyInsInfoForRecommendation(BaseModel):
    company_uuid:str
    company_name:str
    description:str
    category:str