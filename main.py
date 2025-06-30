from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from typing import List
from models import Base, Book, Review
from pydantic import BaseModel
import json
import fakeredis

DATABASE_URL = "sqlite:///./app.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

app = FastAPI(title="Book Review Service")

# Initialize mock Redis
redis_client = fakeredis.FakeStrictRedis()

# Pydantic Schemas
class BookCreate(BaseModel):
    title: str
    author: str

class BookOut(BaseModel):
    id: int
    title: str
    author: str
    model_config = {"from_attributes": True}

class ReviewCreate(BaseModel):
    reviewer: str
    content: str

class ReviewOut(BaseModel):
    id: int
    reviewer: str
    content: str
    model_config = {"from_attributes": True}

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/books", response_model=List[BookOut])
def list_books(db: Session = Depends(get_db)):
    try:
        cached_books = redis_client.get("books")
        if cached_books:
            return json.loads(cached_books)
    except Exception as e:
        # Log error, fallback to DB
        print(f"Cache error: {e}")
    books = db.query(Book).all()
    books_data = [BookOut.model_validate(book).model_dump() for book in books]
    try:
        redis_client.set("books", json.dumps(books_data))
    except Exception as e:
        print(f"Cache error: {e}")
    return books_data

@app.post("/books", response_model=BookOut)
def add_book(book: BookCreate, db: Session = Depends(get_db)):
    db_book = Book(title=book.title, author=book.author)
    db.add(db_book)
    db.commit()
    db.refresh(db_book)
    try:
        redis_client.delete("books")
    except Exception as e:
        print(f"Cache error: {e}")
    return db_book

@app.get("/books/{book_id}/reviews", response_model=List[ReviewOut])
def list_reviews(book_id: int, db: Session = Depends(get_db)):
    book = db.query(Book).filter(Book.id == book_id).first()
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    return db.query(Review).filter(Review.book_id == book_id).all()

@app.post("/books/{book_id}/reviews", response_model=ReviewOut)
def add_review(book_id: int, review: ReviewCreate, db: Session = Depends(get_db)):
    book = db.query(Book).filter(Book.id == book_id).first()
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    db_review = Review(book_id=book_id, reviewer=review.reviewer, content=review.content)
    db.add(db_review)
    db.commit()
    db.refresh(db_review)
    return db_review 