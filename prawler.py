# -*- coding: utf-8 -*-
import requests
import mysql.connector
import pickle
import hashlib
import os
import datetime

from bs4 import BeautifulSoup
from urllib.parse import urljoin

# ===================================================================================================
class page:

    @staticmethod
    def connect(url, timeout = 10):
        req_inst = requests.get(url=url, timeout=timeout)
        headers  = dict(req_inst.headers)
        content  = req_inst.content
        # content_type = req_inst.headers['content-type']
        return page.create_page_instance(url, headers, content)

    @staticmethod
    def read_latest(url, basedir):
        if basedir == None or basedir == "":
            raise ValueError("basedir is set.")
        if not os.path.isdir(basedir) :
            raise ValueError("basedir is not dir. basedir=[{0}]".format(basedir))
        if not basedir.endswith("/"):
            basedir = basedir + "/"
        urlhash = page.__url_to_hash(url)
        basedir = basedir + urlhash + "/"
        if not os.path.isdir(basedir) :
            raise ValueError("specified url is not saved. url=[{0}] dir=[{1}]".format(url, basedir))
        dir_list = page.__get_dir_list(basedir)
        basedir = basedir + dir_list[0]
        return page.read(url, basedir)
        
    @staticmethod
    def read(url, dir):
        if dir == None or dir == "":
            raise ValueError("dir is set.")
        if not os.path.isdir(dir) :
            raise ValueError("dir is not dir. dir=[{0}]".format(dir))
        if not dir.endswith("/"):
            dir = dir + "/"
        with open(dir + page.__get_headers_dump_file_name() , 'rb') as f_headers:
            headers = pickle.loads(f_headers.read())
        with open(dir + page.__get_content_file_name() , 'rb') as f_content:
            content = f_content.read()
        return page.create_page_instance(url, headers, content)
        
    @staticmethod
    def __url_to_hash(url):
        return hashlib.md5(url.encode('utf-8')).hexdigest() 

    @staticmethod
    def __get_content_file_name():
        return "content"

    @staticmethod
    def __get_headers_dump_file_name():
        return "headers.dmp"

    @staticmethod
    def __get_headers_txt_file_name():
        return "headers.txt"
     
    @staticmethod
    def create_page_instance(url, header, content):
        content_type = {v for k,v in header.items() if k.lower() == "content-type"}.pop() # filter(lambda k,v: if k.lo) header['content-type']
        if content_type == None :
            return page(url, header, content)
        elif "text/html" in content_type :
            return html_page(url, header, content)
        else:
            return page(url, header, content)

    @staticmethod
    def __get_dir_list(dir):
        return list(filter(lambda dir_file: os.path.isdir(dir + dir_file), os.listdir(path=dir)))

    def __init__(self, url, header, content):
        self.url = url
        self.headers = header
        self.content = content


    def save(self, basedir):
        if basedir == None or basedir == "":
            raise ValueError("basedir is set.")
        if not os.path.isdir(basedir) :
            raise ValueError("basedir is not dir. basedir=[{0}]".format(basedir))
        if not basedir.endswith("/"):
            basedir = basedir + "/"
        urlhash = page.__url_to_hash(self.url)
        basedir = basedir + urlhash + "/"
        if not os.path.isdir(basedir) :
            os.makedirs(basedir)
            with open(basedir + "url", "w") as f_url:
                f_url.write(self.url)
        basedir = basedir + datetime.datetime.now().strftime('%Y%m%d%H%M%S') + "/"
        os.makedirs(basedir)
        with open(basedir + self.__get_content_file_name(), "wb") as f_content:
            f_content.write(self.content)
        with open(basedir + self.__get_headers_dump_file_name(), "wb") as f_headers:
            f_headers.write(pickle.dumps(self.headers))
        with open(basedir + self.__get_headers_txt_file_name(), "w") as f_headers:
            for key, value in self.headers.items():
                f_headers.write("\"" + key +"\",\"" + value + "\"\n")


# ===================================================================================================
class html_page(page):

    def __init__(self, url, header, content):
        super().__init__(url = url, header = header, content = content)
        self.soup = BeautifulSoup(self.content, "html.parser")

    def get_title(self):
        """
        
        :return:
        """
        return self.soup.find("title").get_text()

    def get_element(self, selector):
        """
        引数に指定された要素を取得

        参考:https://qiita.com/Chanmoro/items/db51658b073acddea4ac
             https://www.pynote.info/entry/beautiful-soup-find-elements
             https://python.civic-apps.com/beautifulsoup4-selector/
             http://python.zombie-hunting-club.com/entry/2017/11/08/192731
        Parameters
        ----------
        selector : str
            取得対象の要素
            div配下のp2クラスを取得する場合、"div > .p2"

        Returns
        -------
        element : 
            取得結果
        """

        # ====================================================================================================
        # 子要素        soup.head
        # タグ全検索        soup.find_all('li')
        # 1件検索        soup.find('li')
        # 属性検索        soup.find('li', href='html://www.google.com/')
        # class検索        soup.find('a', class_=’first'
        # 属性取得        first_link_element['href']
        # テキスト要素        first_link_element.string
        # 親要素        first_link_element.parent
        # ====================================================================================================
        # select_element_list = self.soup.find_all(selector)

        # ====================================================================================================
        # タグ検索        soup.select('li')
        # 1件検索        soup.select_one('li')
        # 属性検索        soup.select('a[href='"'http://www.google.com']')
        # 属性存在        soup.select('a[data])
        # class検索        soup.select('a.first')
        # ====================================================================================================
        return element_list( self, self.soup.select(selector) )

# ===================================================================================================
class element_list:

    def __init__(self, page, bs_element_list):

        self.element_list = list()
        if bs_element_list != None :
            for bs_element in bs_element_list:
                self.element_list.append( self.__create_element( page, bs_element ) )

    def roop(self, func):
        for element in self.element_list:
            func(element)

    def __create_element(self, page, bs_element):
        if bs_element.name == "a":
            return anchor_html_element(page, bs_element)
        else:
            return html_element(page, bs_element)

# ===================================================================================================
class html_element:

    def __init__(self, page, bs_element):
        self.page       = page
        self.bs_element = bs_element

    def content(self):
        return self.bs_element.get_text()

# ===================================================================================================
class anchor_html_element(html_element):

    def __init__(self, page, bs_element):
        super().__init__(page, bs_element)

    def get_href(self):
        href = self.bs_element["href"]
        if href != "" :
            return urljoin(self.page.url, href)
        return None

# ===================================================================================================
class datastore_mysql:
    """
    Mysqlデータベース操作のためのクラス
    """
    def __init__(self, host = "127.0.0.1", port = 43306, username = "test_user", password = "pass123", database = "test_db"):
        self.connection = mysql.connector.connect(host = host, port = port, user=username, password = password, database = database)
        self.connection.ping(reconnect=True)

    def select(self, sql):
        """
        引数のSQLを実行してデータベースからレコードを取得し、メモリに読み込む。
        （全レコードをメモリに取得するため、件数に注意）

        取得したレコードは以下で参照できる。

        ・複数レコードの場合
        for row in rows:
            print(row)
        """
        cursor = self.connection.cursor()
        cursor.execute(sql)
        result = cursor.fetchall()
        cursor.close()
        return result

    def insert(self, sql, values):
        """
        レコードを登録

        例：
        insert("INSERT INTO test_table VALUES (%s, %s, %s)", (3 ,'XEM', 2500))

        Parameters
        ----------
        sql : str
            SQL（文字列）
        values : taple
            登録データ
        """
        cursor = self.connection.cursor()
        cursor.execute(sql, values)
        cursor.close()
        
    def commit(self):
        self.connection.commit()

    def rollback(self):
        self.connection.rollback()

    def __enter__(self):
        return self
    
    def __exit__(self, exception_type, exception_value, traceback):
        self.connection.close()

# ===================================================================================================
class prawler_datastore_mysql(datastore_mysql):
    def __init__(self, host = "127.0.0.1", port = 43306, username = "test_user", password = "pass123", database = "test_db"):
        super().__init__(host, port, )




# ds = datastore_mysql()
# ds.insert("insert into USERS values(%s, %s)", ("aaa", 11))
# rows = ds.select("select * from USERS")
# for row in rows:
#     print(row[0] + str(row[1]))
# page = page.connect("http://gigazine.net")
# print(type(page.content))
# print(type(page.headers))
# element_list = page.get_element("div.content section div.card h2 span")
# def print_content(element):
#     print ( element.content() )
# element_list.roop(print_content)
# page.save("/tmp")

page_inst = page.read_latest("http://gigazine.net", "/tmp")
element_list = page_inst.get_element("div.content section div.card h2 span")
def print_content(element):
    print ( element.content() )
element_list.roop(print_content)
