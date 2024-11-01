from pydantic import BaseModel

class CompanyWithKeyword(BaseModel):
    company_name:str
    keywords:str