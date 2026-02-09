import os
import requests
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from dotenv import load_dotenv

# 自分で作ったファイルから設定を読み込む
from database import engine, get_db
import models

# データベースのテーブルを作成
models.Base.metadata.create_all(bind=engine)

load_dotenv()
API_KEY = os.getenv("GOOGLE_BOOKS_API_KEY")

app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "データベース連携完了！本を登録できます。"}

# 本を検索して、自動でデータベースに保存する魔法のルート
@app.get("/register/{isbn}")
def register_book(isbn: str, db: Session = Depends(get_db)):
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