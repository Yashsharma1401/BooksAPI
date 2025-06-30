from sqlalchemy import Column, Integer, String, ForeignKey, Text, Index
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

class Book(Base):
    __tablename__ = 'books'
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    author = Column(String, nullable=False)
    reviews = relationship('Review', back_populates='book', cascade="all, delete-orphan")

class Review(Base):
    __tablename__ = 'reviews'
    id = Column(Integer, primary_key=True, index=True)
    book_id = Column(Integer, ForeignKey('books.id'), nullable=False, index=True)
    reviewer = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    book = relationship('Book', back_populates='reviews')

Index('ix_reviews_book_id', Review.book_id) 