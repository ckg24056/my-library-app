# Python 3.9の軽量版を使用
FROM python:3.9-slim

# コンテナ内の作業ディレクトリを設定
WORKDIR /app

# 必要なライブラリをインストールするための準備
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# プログラムをコピー
COPY . .

# FastAPIを起動
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]