import time

import redis.asyncio as redis
from datetime import date, timedelta
from typing import List
from fastapi import FastAPI, Depends, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi_limiter import FastAPILimiter
from sqlalchemy.orm import Session
from sqlalchemy import text

from src.database.connect import get_db
from src.database.models import Contact
from src.routes import contacts, auth
from src.schemas import ContactDb

app = FastAPI()

origins = ["http://127.0.0.1:3000"]


app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["Process-Time"] = str(process_time)
    return response


@app.on_event("startup")
async def startup():
    r = await redis.Redis(
        host="localhost", port=6379, db=0, encoding="utf-8", decode_responses=True
    )
    await FastAPILimiter.init(r)


@app.get("/api/healthchecker")
def healthchecker(db: Session = Depends(get_db)):
    try:
        result = db.execute(text("SELECT 1")).fetchone()
        if result is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Database is not configured correctly",
            )
        return {"message": "Welcome to FastAPI!"}
    except Exception as e:
        print(e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error connecting to the database",
        )


@app.get("/", name="Info page")
def info():
    return {"message": "Welcome to Address Book"}


@app.get(
    "/bdays",
    response_model=List[ContactDb],
    name="Bdays in the next 7 days",
    tags=["search"],
)
async def show_bdays(db: Session = Depends(get_db)):
    current_date = date.today()
    delta = timedelta(days=7)
    contacts = db.query(Contact).all()

    bdays_in_next_days = [
        contact for contact in contacts if contact.birthday - current_date <= delta
    ]

    if bdays_in_next_days == False:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")

    return bdays_in_next_days


app.include_router(auth.router, prefix="/api")
app.include_router(contacts.router, prefix="/api")
