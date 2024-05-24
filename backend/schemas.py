# schemas.py
from pydantic import BaseModel
from typing import List

class UserBase(BaseModel):
    firstName: str
    lastName: str
    email: str
    password: str

class UserCreate(UserBase):
    pass

class UserUpdate(UserBase):
    pass

class User(UserBase):
    id: int

    class Config:
        orm_mode = True

class LoginUser(BaseModel):
    email: str
    password: str

class TicketBase(BaseModel):
    departure: str
    departure_airport: str
    departure_airport_code: str
    destination: str
    destination_airport: str
    destination_airport_code: str
    departure_date: str
    destination_date: str
    departure_time: str
    destination_time: str
    duration: str
    airline: str
    flightClass: str
    price: float

class TicketCreate(TicketBase):
    pass

class TicketUpdate(TicketBase):
    pass

class Ticket(TicketBase):
    id: int

    class Config:
        orm_mode = True

class Flight(BaseModel):
    id: int
    departure: str
    departure_airport: str
    departure_airport_code: str
    destination: str
    destination_airport: str
    destination_airport_code: str
    departure_date: str
    destination_date: str
    departure_time: str
    destination_time: str
    duration: str
    airline: str
    flightClass: str
    price: float

class PaginatedFlights(BaseModel):
    totalItems: int
    totalPages: int
    currentPage: int
    flights: List[Flight]