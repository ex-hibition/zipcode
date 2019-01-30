FROM python:3.7-slim

# 日本時間設定
ENV TZ=Asia/Tokyo

# pipenvインストール
RUN pip install pipenv

# ソース配置
RUN mkdir -p /usr/local/app
COPY . /usr/local/app
WORKDIR /usr/local/app

# Python依存ライブラリをインストール
## pip-18.1だとエラーになるのでpip-18.0をインストール
RUN pipenv run pip install pip==18.0
RUN pipenv install

# アプリケーション起動
CMD pipenv run start
