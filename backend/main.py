from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from passlib.context import CryptContext
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
from database import get_db, engine
from models import Base, User as UserModel, Ticket as TicketModel, Flight as FlightModel
from models import Message, Token_Message, CustomOAuth2PasswordRequestForm, PurchaseInput, PasswordChange
from schemas import User as UserSchema, UserCreate, UserUpdate, Ticket as TicketSchema, TicketCreate, TicketUpdate, LoginUser
from schemas import PaginatedFlights
from sqlalchemy.future import select
from sqlalchemy.orm import Session
from contextlib import asynccontextmanager
import traceback
from sqlalchemy import and_, select, func
from jwt import PyJWTError, decode
import secrets
from jose import jwt
from datetime import datetime, timedelta, timezone
import os
from dotenv import load_dotenv
import math

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

async def authenticate_user(db: Session, email: str, password: str):
    stmt = select(UserModel).where(UserModel.email == email)
    result = await db.execute(stmt)
    user = result.scalars().first()
    if not user or user.password != password:  # compare the passwords directly
        return False
    return user

@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        # 데이터베이스 테이블 생성
        await conn.run_sync(Base.metadata.create_all)
    
    try:
        yield  # 여기에서 FastAPI 앱이 실행되는 동안 컨텍스트를 유지합니다.
    finally:
        # 비동기 데이터베이스 연결 종료
        await engine.dispose()

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm="HS256")
    return encoded_jwt

app = FastAPI(lifespan=lifespan)

origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/signup", response_model=Message)
async def create_user(user: UserCreate, db: Session = Depends(get_db)):
    try:
        user = UserModel(**user.dict())
        db.add(user)
        await db.commit()
        await db.refresh(user)
        return {"message": "회원가입 성공"}
    except Exception as e:
        print(f"An error occurred: {e}")    
        traceback.print_exc()
        return {"message": "An error occurred during signup"}
    
@app.post("/login", response_model=Token_Message)
async def login(form_data: CustomOAuth2PasswordRequestForm, db: Session = Depends(get_db)):
    try:
        user = await authenticate_user(db, form_data.email, form_data.password)

        print(f"User data : {user}")
        result = await db.execute(select(UserModel).where(and_(UserModel.email == user.email, UserModel.password == user.password)))
        user = result.scalars().first()
        if not user:
            raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
        access_token_expires = timedelta(minutes=15)
        access_token = create_access_token(
            data={"sub": user.email}, expires_delta=access_token_expires
        )
        return {"message": "로그인 성공", "token": {"access_token": access_token, "token_type": "bearer"}, "user": user.email}
    except Exception as e:
        print(f"An error occurred: {e}")
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal Server Error",
        )

async def get_current_user(db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    print(f"Token: {token}")
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode(token, SECRET_KEY, algorithms=["HS256"])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except PyJWTError as e:
        print(f"Error decoding token: {e}")
        raise credentials_exception
    stmt = select(UserModel).where(UserModel.email == email)
    result = await db.execute(stmt)
    user = result.scalars().first()
    if user is None:
        raise credentials_exception
    return user

from sqlalchemy import delete
@app.delete("/delete/{uid}", status_code=204)
async def delete_user(uid: str, db: Session = Depends(get_db), current_user: str = Depends(get_current_user)):
    print("CURRENT_USER: ", current_user)
    try:
        stmt = delete(UserModel).where(UserModel.email == uid)
        result = await db.execute(stmt)

        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail="User not found")
        await db.commit()
        return {"message": "User deleted successfully"}
    except Exception as e:
        print(f"An error occurred: {e}")
        traceback.print_exc()
        return {"message": "An error occurred during deletion"}


@app.post("/purchase/{flightId}")
async def purchase_ticket(flightId: int, purchase:PurchaseInput, db: Session = Depends(get_db), current_user: UserModel = Depends(get_current_user)):
    try:
        stmt = select(FlightModel).where(FlightModel.id == purchase.flightId)
        result = await db.execute(stmt)
        flight = result.scalars().first()
        if not flight:
            raise HTTPException(status_code=404, detail="Flight not found")
        
        flight_dict = {k: v for k, v in flight.__dict__.items() if not k.startswith('_sa_instance_state')}
        flight_dict["user_id"] = current_user.id
        ticket = TicketModel(**flight_dict)

        db.add(ticket)
        await db.commit()
        await db.refresh(ticket)
        return {"message": "구매 완료", "ticket":ticket}
    except Exception as e:
        print(f"An error occurred: {e}")
        traceback.print_exc()
        return {"message": "An error occurred during ticket purchase"}

@app.get("/tickets")
async def get_tickets(db: Session = Depends(get_db), page: int = 1, limit: int = 10, current_user: UserModel = Depends(get_current_user)):
    stmt = select(TicketModel).where(TicketModel.user_id == current_user.id)
    result = await db.execute(stmt)
    tickets = result.scalars().all()

    query = select(TicketModel)
    total_items = await db.execute(select(func.count()).select_from(query.subquery()))
    total_items = total_items.scalar_one()
    total_pages = math.ceil(total_items / limit)
    return {"totalItems": total_items,
    "totalPages": total_pages,
    "currentPage": page,
    "tickets":tickets}

@app.post("/tickets/{ticketId}/refund")
async def refund_ticket(ticketId: int, db: Session = Depends(get_db), current_user: UserModel = Depends(get_current_user)):
    try:
        stmt = delete(TicketModel).where(TicketModel.id == ticketId)
        result = await db.execute(stmt)
        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail="Ticket not found")
        await db.commit()
        return {"message": "티켓이 환불되었습니다."}
    except Exception as e:
        print(f"An error occurred: {e}")
        traceback.print_exc()
        return {"message": "An error occurred during ticket refund"}

@app.post("/change-password")
async def change_password(password_change: PasswordChange, db: Session = Depends(get_db), current_user: UserModel = Depends(get_current_user)):
    try:
        stmt = select(UserModel).where(UserModel.id == current_user.id)
        result = await db.execute(stmt)
        user = result.scalars().first()

        if password_change.oldPassword != user.password:
            return {"message": "기존 비밀번호가 일치하지 않습니다."
                    }
        user.password = password_change.newPassword
        await db.commit()
        return {"message": "비밀번호가 변경되었습니다."}
    except Exception as e:
        print(f"An error occurred: {e}")
        traceback.print_exc()
        return {"message": "An error occurred during password change"}

@app.get("/flights", response_model=PaginatedFlights)
async def get_flights(
    departures: str = None,
    arrivals: str = None,
    departure_date: str = None,
    arrival_date: str = None,
    page: int = 1,
    limit: int = 5,
    flightClass: str = None,
    airline: str = None,
    db: Session = Depends(get_db)):
    query = select(FlightModel)

    if departures:
        query = query.where(FlightModel.departure == departures)
    if arrivals:
        query = query.where(FlightModel.destination == arrivals)
    if departure_date:
        query = query.where(FlightModel.departure_date == departure_date)
    if arrival_date:
        query = query.where(FlightModel.destination_date == arrival_date)
    if flightClass:
        query = query.where(FlightModel.flightClass == flightClass)
    if airline:
        query = query.where(FlightModel.airline == airline)

    total_items = await db.execute(select(func.count()).select_from(query.subquery()))
    total_items = total_items.scalar_one()
    total_pages = math.ceil(total_items / limit)

    query = query.limit(limit).offset((page - 1) * limit)

    result = await db.execute(query)
    flights = result.scalars().all()

    if not flights:
        raise HTTPException(status_code=404, detail="No flights found")

    return {
    "totalItems": total_items,
    "totalPages": total_pages,
    "currentPage": page,
    "flights": [
        {
            "id": flight.id,
            "departure": flight.departure,
            "departure_airport": flight.departure_airport,
            "departure_airport_code": flight.departure_airport_code,
            "destination": flight.destination,
            "destination_airport": flight.destination_airport,
            "destination_airport_code": flight.destination_airport_code,
            "departure_date": flight.departure_date,
            "destination_date": flight.destination_date,
            "departure_time": flight.departure_time,
            "destination_time": flight.destination_time,
            "duration": flight.duration,
            "airline": flight.airline,
            "flightClass": flight.flightClass,
            "price": flight.price
        } for flight in flights
    ]}