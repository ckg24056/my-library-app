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
    return {"message": "データベース連携完了！本を登録できます。"}


# main.py の既存の read_books を修正
@app.get("/books")
def read_books(request: Request, q: str = None, db: Session = Depends(get_db)):
    # 検索キーワード(q)がある場合はフィルタリング、ない場合は全件取得
    query = db.query(models.Book)
    if q:
        # タイトル または 著者名 にキーワードが含まれているものを探す
        query = query.filter(
            (models.Book.title.contains(q)) | (models.Book.authors.contains(q))
        )
    
    books = query.all()
    return templates.TemplateResponse("books.html", {"request": request, "books": books, "search_query": q})


# 本を検索して、自動でデータベースに保存する魔法のルート
# main.py の登録処理を修正
@app.get("/register/{isbn}")
def register_book(isbn: str, db: Session = Depends(get_db)):
    # 1. すでにそのISBNの本が登録されていないかチェック
    existing_book = db.query(models.Book).filter(models.Book.isbn == isbn).first()
    if existing_book:
        return {"message": "その本はすでに本棚にあります"}

    # 2. なければAPIで検索して登録（今までの処理）
    # ...（以下、既存の検索・保存コード）
    # 1. Google Books APIに問い合わせ
    url = f"https://www.googleapis.com/books/v1/volumes?q=isbn:{isbn}&key={API_KEY}"
    response = requests.get(url)
    data = response.json()
    
    if "items" not in data:
        raise HTTPException(status_code=404, detail="本が見つかりませんでした")

    # 2. 必要な情報を抜き出す
    volume_info = data["items"][0]["volumeInfo"]
    title = volume_info.get("title", "不明なタイトル")
    # 著者はリスト形式なので、カンマ区切りの文字列に変換
    authors = ", ".join(volume_info.get("authors", ["不明な著者"]))
    categories = ", ".join(volume_info.get("categories", ["未分類"]))
    thumbnail = volume_info.get("imageLinks", {}).get("thumbnail", "")

    # 3. データベースに保存するためのデータを作成
    new_book = models.Book(
        isbn=isbn,
        title=title,
        authors=authors,
        categories=categories,
        thumbnail=thumbnail,
        location="未設定", # 初期値
        read_count=0      # 初期値
    )

    # 4. データベースに書き込む
    try:
        db.add(new_book)
        db.commit() # 確定！
        db.refresh(new_book)
        return {"message": "登録成功！", "book": new_book}
    except Exception as e:
        db.rollback() # エラーが起きたら元に戻す
        return {"error": "既に登録されているか、エラーが発生しました", "detail": str(e)}

# 削除用API
@app.delete("/delete/{book_id}")
def delete_book(book_id: int, db: Session = Depends(get_db)):
    book = db.query(models.Book).filter(models.Book.id == book_id).first()
    if book:
        db.delete(book)
        db.commit()
        return {"message": "削除しました"}
    return {"message": "本が見つかりませんでした"}, 404


# 更新用API（場所や読書回数を変更する）
@app.put("/update/{book_id}")
def update_book(book_id: int, location: str = None, read_count: int = None, db: Session = Depends(get_db)):
    book = db.query(models.Book).filter(models.Book.id == book_id).first()
    if not book:
        return {"message": "本が見つかりませんでした"}, 404
    
    # 送られてきたデータがあれば更新する
    if location is not None:
        book.location = location
    if read_count is not None:
        book.read_count = read_count
        
    db.commit()
    return {"message": "更新しました", "location": book.location, "read_count": book.read_count}