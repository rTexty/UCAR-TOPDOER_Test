from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
from typing import List, Optional
import sqlite3
from datetime import datetime
import os

DB_PATH = 'reviews.db'

app = FastAPI()

# --- Модель для входящих данных ---
class ReviewIn(BaseModel):
    text: str

# --- Модель для ответа ---
class ReviewOut(BaseModel):
    id: int
    text: str
    sentiment: str
    created_at: str

# --- Словари для определения тональности ---
POSITIVE = ["хорош", "люблю"]
NEGATIVE = ["плохо", "ненавиж"]

def get_sentiment(text: str) -> str:
    t = text.lower()
    if any(word in t for word in POSITIVE):
        return "positive"
    if any(word in t for word in NEGATIVE):
        return "negative"
    return "neutral"

# --- Инициализация БД ---
def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS reviews (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                text TEXT NOT NULL,
                sentiment TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            """
        )

@app.on_event("startup")
def startup():
    init_db()

# --- POST /reviews ---
@app.post("/reviews", response_model=ReviewOut)
def create_review(review: ReviewIn):
    sentiment = get_sentiment(review.text)
    created_at = datetime.utcnow().isoformat()
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.execute(
            "INSERT INTO reviews (text, sentiment, created_at) VALUES (?, ?, ?)",
            (review.text, sentiment, created_at)
        )
        review_id = cursor.lastrowid
    return {
        "id": review_id,
        "text": review.text,
        "sentiment": sentiment,
        "created_at": created_at
    }

# --- GET /reviews?sentiment=negative ---
@app.get("/reviews", response_model=List[ReviewOut])
def get_reviews(sentiment: Optional[str] = Query(None, regex="^(positive|negative|neutral)$")):
    query = "SELECT id, text, sentiment, created_at FROM reviews"
    params = ()
    if sentiment:
        query += " WHERE sentiment = ?"
        params = (sentiment,)
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.execute(query, params)
        rows = cursor.fetchall()
    return [
        {"id": row[0], "text": row[1], "sentiment": row[2], "created_at": row[3]}
        for row in rows
    ]
