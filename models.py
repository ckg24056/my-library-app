from sqlalchemy import Column, Integer, String, Text
from database import Base

# データベースの「テーブル」の設計図
class Book(Base):
    __tablename__ = "books"

    id = Column(Integer, primary_key=True, index=True)
    isbn = Column(String(13), unique=True, index=True) # ISBNは重ならないように
    title = Column(String(200))
    authors = Column(Text)       # 複数を想定してText型
    categories = Column(Text)    # 複数を想定してText型
    thumbnail = Column(Text)     # 画像URL
    location = Column(String(100)) # 保管場所
    read_count = Column(Integer, default=0) # 読了回数