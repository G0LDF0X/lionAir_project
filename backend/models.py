# models.py
from sqlalchemy import Column, Integer, String, Float, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from pydantic import BaseModel
from typing import Optional, List
Base = declarative_base()

class Message(BaseModel):
    message: str

class Token_Message(Message):
    token: dict
    user: str

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, index=True)
    firstName = Column(String, index=True)
    lastName = Column(String, index=True)
    email = Column(String, index=True)
    password = Column(String)


class Ticket(Base):
    __tablename__ = 'tickets'
    id = Column(Integer, primary_key=True, index=True)
    departure = Column(String, index=True)
    departure_airport = Column(String, index=True)
    departure_airport_code = Column(String, index=True)
    destination = Column(String, index=True)
    destination_airport = Column(String, index=True)
    destination_airport_code = Column(String, index=True)
    departure_date = Column(String, index=True)
    destination_date = Column(String, index=True)
    departure_time = Column(String, index=True)
    destination_time = Column(String, index=True)
    duration = Column(String, index=True)
    airline = Column(String, index=True)
    flightClass = Column(String, index=True)
    price = Column(Float, index=True)
    user_id = Column(Integer, ForeignKey('users.id'))

class Flight(Base):
    __tablename__ = 'flights'
    id = Column(Integer, primary_key=True, index=True)
    departure = Column(String, index=True)
    departure_airport = Column(String, index=True)
    departure_airport_code = Column(String, index=True)
    destination = Column(String, index=True)
    destination_airport = Column(String, index=True)
    destination_airport_code = Column(String, index=True)
    departure_date = Column(String, index=True)
    destination_date = Column(String, index=True)
    departure_time = Column(String, index=True)
    destination_time = Column(String, index=True)
    duration = Column(String, index=True)
    airline = Column(String, index=True)
    flightClass = Column(String, index=True)
    price = Column(Float, index=True)
    
class CustomOAuth2PasswordRequestForm(BaseModel):
    email: str
    password: str

class PurchaseInput(BaseModel):
    flightId: int
    userId: str

class PasswordChange(BaseModel):
    oldPassword: str
    newPassword: str