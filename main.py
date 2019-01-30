from flask import Flask, render_template, abort, request
from flask_bootstrap import Bootstrap
from boto3.dynamodb.conditions import Key
from flask_nav import Nav
from flask_nav.elements import Navbar, View
import boto3
import csv
import logging
import requests
import os
import zipfile

app = Flask(__name__)
Bootstrap(app)

logger = logging.getLogger(__name__)
dynamo = boto3.resource('dynamodb', endpoint_url='http://localhost:8000')

nav = Nav()


@nav.navigation()
def target_navbar():
    return Navbar(
        'Zipcode',
        View(text='Search', endpoint='top'),
        View(text='View', endpoint='view'),
        View(text='Init', endpoint='init'),
    )


nav.init_app(app)


@app.route("/", methods=['GET', 'POST'])
def index():
    return render_template('search.htm')


@app.route("/top", methods=['GET', 'POST'])
def top():
    return render_template('search.htm')


@app.route("/init", methods=['GET', 'POST'])
def init():
    """住所データをdynamodbにセットする"""
    try:
        table_name = 'zipcode'
        table = dynamo.Table(table_name)

        # 郵便番号一覧を取得
        zipcode_url = 'https://www.post.japanpost.jp/zipcode/dl/kogaki/zip/ken_all.zip'
        zipcode_zip = os.path.basename(zipcode_url)
        url_object = requests.get(zipcode_url)
        # ZIPファイル取得
        with open(zipcode_zip, 'wb') as file:
            file.write(url_object.content)
        # ZIPファイル解凍
        with zipfile.ZipFile(zipcode_zip) as target_zipfile:
            target_zipfile.extractall()

        # csvヘッダー定義
        header_list = ['group_code', 'zipcode5', 'zipcode7',
                       'ward_kana', 'city_kana', 'town_kana',
                       'ward', 'city', 'town',
                       'flg_1', 'flg_2', 'flg_3', 'flg_4', 'flg_5', 'flg_6',
                       ]

        with table.batch_writer() as batch:
            with open('./KEN_ALL.CSV', encoding='shift_jis', newline='') as csvfile:
                reader = csv.DictReader(csvfile, fieldnames=header_list)
                for row in reader:
                    # print(f'row={row}')
                    batch.put_item(
                        Item={
                            # hash key (ホットキー)
                            'data_type': 'zipcode',
                            # range key
                            'complex_key': f"{row['zipcode7']}#{row['city']}#{row['town']}#{row['flg_3']}",
                            'group_code': row['group_code'],
                            'zipcode7': row['zipcode7'],
                            'zipcode5': row['zipcode5'],
                            'ward': row['ward'],
                            'city': row['city'],
                            'town': row['town'],
                            'ward_kana': row['ward_kana'],
                            'city_kana': row['city_kana'],
                            'town_kana': row['town_kana'],
                            # 'flg_1': row['flg_1'],
                            # 'flg_2': row['flg_2'],
                            # 'flg_3': row['flg_3'],
                            # 'flg_4': row['flg_4'],
                            # 'flg_5': row['flg_5'],
                            # 'flg_6': row['flg_6'],
                        }
                    )
        return 'init database.'

    except Exception as err:
        logger.exception(err)
        abort(500)


@app.route("/view", methods=['GET', 'POST'])
def view():
    """一覧表示"""
    table_name = 'zipcode'
    table = dynamo.Table(table_name)

    # TODO:1MB制限対応
    res = table.scan()
    # zipcode7でソート
    res_dict_list = sorted(res['Items'], key=lambda x: x['zipcode7'])
    return render_template('view.htm', res_dict_list=res_dict_list)


@app.route("/search", methods=['GET', 'POST'])
def search():
    """検索ページ"""
    table_name = 'zipcode'
    table = dynamo.Table(table_name)

    res = table.query(
        KeyConditionExpression=Key('data_type').eq('zipcode') & Key('complex_key').begins_with(request.form['key'])
    )

    # zipcode7でソート
    res_dict_list = sorted(res['Items'], key=lambda x: x['zipcode7'])
    return render_template('view.htm', res_dict_list=res_dict_list)


if __name__ == '__main__':
    app.run()
