import os
import uuid
from datetime import timedelta
from typing import List
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from database import get_database_collections
from models import User, BusinessCard, CreateBusinessCard
from utils import hash_password, authenticate_user, create_access_token, verify_token


app = FastAPI()

load_dotenv()
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES"))

users_collection, cards_collection = get_database_collections()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Routes
@app.post("/register", summary="Register a new user")
def register(user: User):
    if users_collection.find_one({"email": user.email}):
        raise HTTPException(status_code=400, detail="Email already registered")
    hashed_password = hash_password(user.password)
    users_collection.insert_one({"email": user.email, "password": hashed_password})
    return {"message": "User registered successfully"}

@app.post("/token", summary="Login to get an access token")
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(data={"sub": user["email"]}, expires_delta=access_token_expires)
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/cards", summary="Create a new business card")
def create_card(card: CreateBusinessCard, token: str = Depends(oauth2_scheme)):
    payload = verify_token(token)
    email = payload.get("sub")
    if not users_collection.find_one({"email": email}):
        raise HTTPException(status_code=404, detail="Invalid User")
    card_dict = card.model_dump()
    card_dict.update({"id": str(uuid.uuid4()), "owner": email})
    result = cards_collection.insert_one(card_dict)
    card_dict["_id"] = str(result.inserted_id)
    return {"message": "Business card created", "card": card_dict}

@app.get("/cards", summary="Retrieve all business cards", response_model=List[BusinessCard])
def get_cards(token: str = Depends(oauth2_scheme)):
    payload = verify_token(token)
    email = payload.get("sub")
    if not users_collection.find_one({"email": email}):
        raise HTTPException(status_code=404, detail="Invalid User")
    cards = cards_collection.find({"owner": email})
    return [BusinessCard(**card) for card in cards]

@app.get("/cards/{card_id}", summary="Retrieve a single business card")
def get_card(card_id: str, token: str = Depends(oauth2_scheme)):
    payload = verify_token(token)
    email = payload.get("sub")
    if not users_collection.find_one({"email": email}):
        raise HTTPException(status_code=404, detail="Invalid User")
    card = cards_collection.find_one({"id": card_id, "owner": email})
    if not card:
        raise HTTPException(status_code=404, detail="Card not found")
    return BusinessCard(**card)

@app.delete("/cards/{card_id}", summary="Delete a business card")
def delete_card(card_id: str, token: str = Depends(oauth2_scheme)):
    payload = verify_token(token)
    email = payload.get("sub")
    if not users_collection.find_one({"email": email}):
        raise HTTPException(status_code=404, detail="Invalid User")
    result = cards_collection.delete_one({"id": card_id, "owner": email})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Card not found")
    return {"message": "Card deleted successfully"}
