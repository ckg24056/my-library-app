from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# データベースファイルの保存場所を指定（同じフォルダ内に db.sqlite3 が作られます）
SQLALCHEMY_DATABASE_URL = "sqlite:///./db.sqlite3"

# データベースに接続するためのエンジンを作成
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

# データベース操作をするための「セッション」を作る設定
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 各モデル（Bookなど）が継承するためのベースクラス
Base = declarative_base()

# データベースセッションを取得するための便利な関数
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()