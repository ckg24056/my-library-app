import os
import requests
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from dotenv import load_dotenv
from fastapi.templating import Jinja2Templates
from fastapi import Request 

# 自分で作ったファイルから設定を読み込む
from database import engine, get_db
import models

# データベースのテーブルを作成
models.Base.metadata.create_all(bind=engine)

load_dotenv()
API_KEY = os.getenv("GOOGLE_BOOKS_API_KEY")

app = FastAPI()
templates = Jinja2Templates(directory="templates")

@app.get("/")
def read_root():
    return {"message": "蔵書管理システムへようこそ！ /books にアクセスしてください。"}

# 蔵書一覧表示（検索機能付き）
@app.get("/books")
def read_books(request: Request, q: str = None, db: Session = Depends(get_db)):
    query = db.query(models.Book)
    if q:
        query = query.filter(
            (models.Book.title.contains(q)) | (models.Book.authors.contains(q))
        )
    books = query.all()
    return templates.TemplateResponse("books.html", {"request": request, "books": books, "search_query": q})

# 書籍登録API（ISBN使用）
@app.get("/register/{isbn}")
def register_book(isbn: str, db: Session = Depends(get_db)):
    try:
        # 1. 既に登録されているか確認
        existing_book = db.query(models.Book).filter(models.Book.isbn == isbn).first()
        if existing_book:
            return {"message": "この本は既に登録されています"}

        # 2. Google Books APIに問い合わせ
        url = f"https://www.googleapis.com/books/v1/volumes?q=isbn:{isbn}&key={API_KEY}"
        response = requests.get(url)
        data = response.json()
        
        if "items" not in data:
            return {"message": "Google Booksで本が見つかりませんでした。ISBNを確認してください。"}

        # 3. 必要な情報を抜き出す
        volume_info = data["items"][0]["volumeInfo"]
        title = volume_info.get("title", "不明なタイトル")
        authors = ", ".join(volume_info.get("authors", ["不明な著者"]))
        categories = ", ".join(volume_info.get("categories", ["未分類"]))
        thumbnail = volume_info.get("imageLinks", {}).get("thumbnail", "")

        # 4. データベースに保存するためのデータを作成
        new_book = models.Book(
            isbn=isbn,
            title=title,
            authors=authors,
            categories=categories,
            thumbnail=thumbnail,
            location="未設定",
            read_count=0
        )

        # 5. データベースに書き込む
        db.add(new_book)
        db.commit()
        db.refresh(new_book)
        
        return {"message": f"「{title}」を登録しました！"}

    except Exception as e:
        db.rollback()
        print(f"Error: {e}")
        return {"message": f"エラーが発生しました: {str(e)}"}

# 削除用API
@app.delete("/delete/{book_id}")
def delete_book(book_id: int, db: Session = Depends(get_db)):
    book = db.query(models.Book).filter(models.Book.id == book_id).first()
    if book:
        db.delete(book)
        db.commit()
        return {"message": "削除しました"}
    return {"message": "本が見つかりませんでした"}

# 更新用API
@app.put("/update/{book_id}")
def update_book(book_id: int, location: str = None, read_count: int = None, db: Session = Depends(get_db)):
    book = db.query(models.Book).filter(models.Book.id == book_id).first()
    if not book:
        return {"message": "本が見つかりませんでした"}
    
    if location is not None:
        book.location = location
    if read_count is not None:
        book.read_count = read_count
        
    db.commit()
    return {"message": "更新しました"}