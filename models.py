from pydantic import BaseModel, EmailStr

class User(BaseModel):
    email: EmailStr
    password: str

class BusinessCard(BaseModel):
    id: str 
    name: str
    title: str
    company: str
    email: EmailStr
    phone: str

class CreateBusinessCard(BaseModel):
    name: str
    title: str
    company: str
    email: EmailStr
    phone: str
