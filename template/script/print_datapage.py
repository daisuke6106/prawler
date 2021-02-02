import os
import sys
import csv
import json
import argparse
import urllib.parse
import codecs

from distutils.util import strtobool
from prawler import time
from prawler import prawler_repository
from prawler import history_file
from prawler import prawler_logger
from prawler import msg
from prawler import page
from prawler import config_file

# ===================================================================================================
# 出力関数
# ===================================================================================================
def print_page_data(page):

    # 日時
    date = page.get_element("time").content()

    # タイトル
    title = page.get_element("title").content()

    # タグ
    tag = page.get_element("span.p-category > a").content()

    # データ本体
    data = page.get_element("div.cntimage").content()

    # print(tag)
    print(json.dumps({"date":date, "title":title, "tag":[tag], "data":data}))
    # print(
    #     codecs.decode(
    #         json.dumps({"date":date, "title":title, "tag":[tag], "data":data}), 
    #         'unicode-escape'
    #     )
    # )


# ===================================================================================================
# メイン
# ===================================================================================================
if __name__ == '__main__':

    #==================================================
    # コマンド引数
    # 参考：https://qiita.com/kzkadc/items/e4fc7bc9c003de1eb6d0
    #==================================================
    argpaese = argparse.ArgumentParser(description="所定のURLを正規化して標準出力に出力する。")
    # 必須オプション
    argpaese.add_argument("url", help="表示対象のURL")
    # 引数を解析
    args = argpaese.parse_args()
    # 引数を取得
    url = args.url
    
    #==================================================
    # カレントディレクトリをリポジトリのホームへ変更
    #==================================================
    os.chdir(os.path.dirname(os.path.abspath(__file__)) + "/../")

    #==================================================
    # リポジトリのセットアップ
    #==================================================
    repository = prawler_repository.setup("./")

    #==================================================
    # 保存済みのページを読み込み
    #==================================================
    lastest_page = repository.read_latest_page(url)

    #==================================================
    # ページデータの出力
    #==================================================
    print_page_data(lastest_page)
