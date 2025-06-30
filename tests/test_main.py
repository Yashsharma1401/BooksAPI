import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from main import app, redis_client, SessionLocal
from models import Book, Review
import pytest
from fastapi.testclient import TestClient

client = TestClient(app)

# Helper to clear cache before tests
def clear_cache():
    try:
        redis_client.delete("books")
    except Exception:
        pass

# Helper to clear the database before tests
def clear_db():
    db = SessionLocal()
    db.query(Review).delete()
    db.query(Book).delete()
    db.commit()
    db.close()

# Unit test: GET /books (should return empty list initially)
def test_get_books_empty():
    clear_db()
    clear_cache()
    response = client.get("/books")
    assert response.status_code == 200
    assert response.json() == []

# Unit test: POST /books (add a book)
def test_post_books():
    clear_cache()
    data = {"title": "Test Book", "author": "Author A"}
    response = client.post("/books", json=data)
    assert response.status_code == 200
    result = response.json()
    assert result["title"] == "Test Book"
    assert result["author"] == "Author A"

# Integration test: GET /books cache-miss path
def test_get_books_cache_miss(monkeypatch):
    clear_cache()
    # Add a book directly
    client.post("/books", json={"title": "Cache Book", "author": "Cache Author"})
    # Clear cache to force miss
    clear_cache()
    # Spy on redis get to simulate cache miss
    called = {"get": False, "set": False}
    orig_get = redis_client.get
    orig_set = redis_client.set
    def fake_get(key):
        called["get"] = True
        return None
    def fake_set(key, value):
        called["set"] = True
        return orig_set(key, value)
    monkeypatch.setattr(redis_client, "get", fake_get)
    monkeypatch.setattr(redis_client, "set", fake_set)
    response = client.get("/books")
    assert response.status_code == 200
    assert any(b["title"] == "Cache Book" for b in response.json())
    assert called["get"]
    assert called["set"] 