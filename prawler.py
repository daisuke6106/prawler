# -*- coding: utf-8 -*-
import requests
import mysql.connector
import pickle
import hashlib
import os
import datetime
import time
import shutil
import subprocess

from bs4 import BeautifulSoup
from urllib.parse import urljoin

# ===================================================================================================
class page:

    @staticmethod
    def connect(url, timeout = 10, logger=None, connect_err_raise = False):
        if logger == None:
            logger = prawler_logger.get_instance()
        try:
            if url == None:
                raise ValueError("url is not set.")
            logger.info(msg("access start url=[{url}]").param(url=url))
            req_inst = requests.get(url=url, timeout=timeout)
            logger.info(msg("connect success url=[{url}]").param(url=url))
            headers  = dict(req_inst.headers)
            content  = req_inst.content
            # content_type = req_inst.headers['content-type']
            return page.create_page_instance(url, headers, content, logger)
        except Exception as e:
            logger.error(e)
            if connect_err_raise :
                raise e

    @staticmethod
    def read_latest(url, basedir, logger=None):
        if logger == None:
            logger = prawler_logger.get_instance()
        if basedir == None or basedir == "":
            raise ValueError("basedir is set.")
        if not os.path.isdir(basedir) :
            raise ValueError("basedir is not dir. basedir=[{0}]".format(basedir))
        if not basedir.endswith("/"):
            basedir = basedir + "/"
        urlhash = page.url_to_hash(url)
        basedir = basedir + urlhash + "/"
        if not os.path.isdir(basedir) :
            raise ValueError("specified url is not saved. url=[{0}] dir=[{1}]".format(url, basedir))
        dir_list = page.__get_dir_list(basedir)
        basedir = basedir + dir_list[0]
        return page.read(url, basedir, logger)
        
    @staticmethod
    def read(url, dir, logger=None):
        if logger == None:
            logger = prawler_logger.get_instance()
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
        return page.create_page_instance(url, headers, content, logger)
        
    @staticmethod
    def url_to_hash(url):
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
    def create_page_instance(url, header, content, logger):
        content_type = {v for k,v in header.items() if k.lower() == "content-type"}.pop() # filter(lambda k,v: if k.lo) header['content-type']
        if content_type == None :
            return page(url, header, content, logger)
        elif "text/html" in content_type :
            return html_page(url, header, content, logger)
        else:
            return page(url, header, content, logger)

    @staticmethod
    def __get_dir_list(dir):
        return list(filter(lambda dir_file: os.path.isdir(dir + dir_file), os.listdir(path=dir)))

    def __init__(self, url, header, content, logger):
        self.url = url
        self.headers = header
        self.content = content
        self.logger = logger

    def save(self, basedir):
        if basedir == None or basedir == "":
            raise ValueError("basedir is set.")
        if not os.path.isdir(basedir) :
            raise ValueError("basedir is not dir. basedir=[{0}]".format(basedir))
        if not basedir.endswith("/"):
            basedir = basedir + "/"
        urlhash = page.url_to_hash(self.url)
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
        self.logger.info(msg("page saved.")
            .detail(
                url = self.url,
                url_hash = urlhash,
                save_dir=basedir
            )
        )


# ===================================================================================================
class html_page(page):

    def __init__(self, url, header, content, logger):
        super().__init__(url = url, header = header, content = content, logger = logger)
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
        
        element_list_result = element_list( self, self.soup.select(selector) )
        self.logger.info(msg("call get_element.")
            .detail(
                selector = selector,
                element_list = [str(element) for element in element_list_result]),
            )
        #for element in element_list_result:
        #    self.logger.info(msg("selected element->{element}").param(element=str(element)))
        return element_list_result

# ===================================================================================================
class element_list:

    def __init__(self, page, bs_element_list):
        self.page = page
        self.element_list = list()
        if bs_element_list != None :
            for bs_element in bs_element_list:
                self.element_list.append( self.__create_element( page, bs_element ) )

    def content(self):
        content = ""
        for element in self.element_list:
            content += element.content()
        return content

    def get_anchor(self):
        apended_anchor_list = list()
        for element in self.element_list:
            anchor_element_list = element.get_anchor()
            for anchor_element in anchor_element_list:
                if anchor_element.get_href() == "":
                    continue
                if self.__has_same_anchor(apended_anchor_list, anchor_element) :
                    continue
                apended_anchor_list.append(anchor_element)
            
        anchor_bs_element_list = list()
        for anchor_element in apended_anchor_list:
            anchor_bs_element_list.append(anchor_element.bs_element)

        return_element_lsit = element_list(self.page, anchor_bs_element_list)
        self.page.logger.info(
            msg("call get_anchor.").detail(
                selected_anchor_list=[str(element) for element in return_element_lsit]
            )
        )
        # for element in return_element_lsit:
        #     self.page.logger.info(msg("selected anchor->{element}").param(element=str(element)))
        return return_element_lsit
    
    def __has_same_anchor(self, appended_anchor_list, check_target_anchor):
        for appended_anchor in appended_anchor_list:
            if appended_anchor.get_href() == check_target_anchor.get_href():
                return True
        return False

    # def get_anchor_str(self):
    #     anchor_str_list = list()
    #     for element in self.get_anchor().element_list:
    #         href = element.get_href()        
    #         if href != None and href != "":
    #             anchor_str_list.append( href )
    #     return anchor_str_list

    def print_href(self):
        for element in self.get_anchor().element_list:
            href = element.get_href()
            if href != None and href != "":
                print ( href )

    def print_element(self):
        for element in self.element_list:
            print ( element )

    def print_content(self):
        for element in self.element_list:
            print ( element.content() )

    def roop(self, func):
        for element in self.element_list:
            func(element)

    def __create_element(self, page, bs_element):
        if bs_element.name == "a":
            return anchor_html_element(page, bs_element)
        else:
            return html_element(page, bs_element)

    def __iter__(self):
        self.__iterator_count = 0
        return self
    
    def __next__(self):
        if self.__iterator_count == len(self.element_list) :
            raise StopIteration()
        return_element = self.element_list[self.__iterator_count]
        self.__iterator_count += 1
        return return_element

# ===================================================================================================
class html_element:

    def __init__(self, page, bs_element):
        self.page       = page
        self.bs_element = bs_element

    def get_attr(self, attr):
        return self.bs_element[attr]

    def content(self):
        return self.bs_element.get_text()

    def get_anchor(self):
        anchor_bs_element_list = self.bs_element.find_all("a")
        return element_list(self.page, anchor_bs_element_list)

    def __str__(self):
        return self.bs_element.prettify().replace("\n","")

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

# ===================================================================================================
from logging import getLogger, FileHandler, StreamHandler, Formatter, DEBUG
import json
class msg:
    def __init__(self, message ):
        self.message    = message
        self.param_dict = None
        self.detail_data = None
    
    def param(self, **param_dict):
        self.param_dict = param_dict
        return self
    
    def detail(self, **detail_data):
        self.detail_data = detail_data
        return self
    
    def __str__(self):
        if self.detail_data is not None:
            if self.param_dict is not None:
                return json.dumps({"body":self.message.format(**self.param_dict), **self.detail_data})
            else:
                return json.dumps({"body":self.message, **self.detail_data})
        else :
            if self.param_dict is not None:
                return json.dumps({"body":self.message.format(**self.param_dict)})
            else:
                return json.dumps({"body":self.message})

class prawler_logger:

    @classmethod
    def get_instance(cls):
        if not hasattr(cls, "_instance") :
            cls._instance = prawler_logger()
        return cls._instance

    def __init__(self):
        # https://docs.python.org/ja/3/library/logging.html#logrecord-attributes
        self.logger = getLogger(__name__)
        self.fotmatter = Formatter(fmt='{"timestamp":"%(asctime)s","process":"%(process)d","level":"%(levelname)s","message":%(message)s}', datefmt='%Y/%m/%d-%H:%M:%S')

        stream_handler = StreamHandler()
        stream_handler.setLevel(DEBUG)
        stream_handler.setFormatter(self.fotmatter)
        self.logger.addHandler(stream_handler)

        self.logger.setLevel(DEBUG)
        self.logger.propagate = False
    
    def add_file_log_handler(self, file_path):
        file_handler = FileHandler(file_path)
        file_handler.setLevel(DEBUG)
        file_handler.setFormatter(self.fotmatter)
        self.logger.addHandler(file_handler)

    def info(self, msg):
        self.logger.info(str(msg))
    
    def error(self, e):
        self.logger.error(e)

class prawler_repository :

    @staticmethod
    def setup(dir_path, logger = None):
        if os.path.exists(dir_path) :
            return prawler_repository.read(dir_path, logger)
        else :
            return prawler_repository.init(dir_path, logger)

    @staticmethod
    def init(dir_path, logger = None):
        if os.path.exists(dir_path) :
            raise ValueError("dir_path is exists. dir_path=[{0}]".format(dir_path))
        # トレイリングスラッシュを補完
        dir_path = dir_path if dir_path[-1] == "/" else dir_path + "/"
        # テンプレートディレクトリをコピー
        shutil.copytree("template", dir_path)
        # このファイルをコピー
        shutil.copyfile(os.path.abspath(__file__), dir_path + "script/prawler.py")
        # GITリポジトリとして登録
        os.chdir(dir_path)
        subprocess.call("git init" , shell=True)
        subprocess.call("git add .", shell=True)
        subprocess.call("git commit -m\"create repository\"", shell=True)
        # github用にmasterブランチの名称をmainへ変更
        subprocess.call("git branch -m master main", shell=True)
        # GITのリモートリポジトリを追加
        # subprocess.call("git remote add origin https://localhost/datarepository/XXXXXX", shell=True)
        # subprocess.call("git push -u origin main", shell=True)

        # インスタンスを生成して返却
        return prawler_repository(dir_path, logger)

    @staticmethod
    def read(dir_path, logger = None):
        if not os.path.exists(dir_path) :
            raise ValueError("dir_path is not exists. dir_path=[{0}]".format(dir_path))
        # トレイリングスラッシュを補完
        dir_path = dir_path if dir_path[-1] == "/" else dir_path + "/"
        # インスタンスを生成して返却
        return prawler_repository(dir_path, logger)

    def __init__(self, dir_path, logger):
        self.dir_path    = dir_path
        self.script_path = dir_path + "script" + "/"
        self.config_path = dir_path + "config" + "/"
        self.logs_path   = dir_path + "logs"   + "/"
        self.data_path   = dir_path + "data"   + "/"
        self.index_path  = dir_path + "index"  + "/"

        if logger == None:
            self.logger = prawler_logger.get_instance()
        else:
            self.logger = logger
        
        self.logger.add_file_log_handler(self.logs_path + "prawler.log")
        self.index_file_obj  = history_file.read( self.index_path + "index")
        self.config_file_obj = config_file.read( self.config_path + "config.ini")

    def setup_index_file(self, name):
        return history_file.setup( self.index_path + name )

    def save(self, page):
        if page == None :
            self.logger.info(msg("page is nothing. page save was skip."))
        else :
            self.index_file_obj.add(page.url)
            page.save(self.data_path)

    def read_latest_page(self, url):
        return page.read_latest(url, self.data_path)

    def is_saved(self, url):
        return os.path.isdir(self.data_path + page.url_to_hash(url) + "/")

    def __enter__(self):
        # 前処理は特になし
        pass

    def __exit__(self, exc_type, exc_value, traceback):
        # 後処理
        #self.index_file_obj.close()
        pass

class file:
    
    @staticmethod
    def create(file_path):
        if os.path.exists(file_path) :
            raise ValueError("file is exists. file_path=[{0}]".format(file_path))
        file_obj = open(file_path, "x", encoding='utf-8')
        file_obj.write("")
        return file(file_path, file_obj)

    def __init__(self, file_path, file_obj):
        self.file_path = file_path
        self.file_obj  = file_obj

    def write(self, write_str):
        self.file_obj.write(write_str)
        self.file_obj.flush()
        return self

    def __enter__(self):
        # 前処理は特になし
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        # 後処理
        self.file_obj.close()

class history :

    def __init__(self):
        self.url_hash_dict = dict()

    def add(self, url_str):
        self.url_hash_dict[url_str] = page.url_to_hash(url_str)

    def is_visited(self, arg_url):
        return arg_url in self.url_hash_dict

class history_file(history, file):

    @staticmethod
    def setup(file_path, logger = None):
        # 相対パスを絶対パスへ変換
        file_path = pathlib.Path(file_path).resolve()
        if os.path.exists(file_path) :
            return history_file.read(file_path)
        else :
            return history_file.create(file_path)

    @staticmethod
    def create(file_path):
        # 相対パスを絶対パスへ変換
        file_path = pathlib.Path(file_path).resolve()
        file_instance = file.create(file_path)
        url_hash_dict = dict()
        return history_file(file_instance.file_path, file_instance.file_obj, url_hash_dict)

    @staticmethod
    def read(file_path):
        # 相対パスを絶対パスへ変換
        file_path = pathlib.Path(file_path).resolve()
        if not os.path.exists(file_path) :
            raise ValueError("file is not exists. file_path=[{0}]".format(file_path))
        file_obj = open(file_path, "r+", encoding='utf-8')
        url_hash_dict = dict()
        for line in file_obj.readlines() :
            splited_line = line.strip().split(" ")
            url_str  = splited_line[0]
            hash_str = splited_line[1]
            url_hash_dict[url_str] = hash_str
        return history_file(file_path, file_obj, url_hash_dict)

    def __init__(self, file_path, file_obj, url_hash_dict):
        history.__init__(self)
        file.__init__(self, file_path, file_obj)
        self.url_hash_dict = url_hash_dict
        
    def add(self, url_str):
        if not self.is_visited(url_str):
            hash_str = page.url_to_hash(url_str)
            self.write(url_str + " " + hash_str + "\n")
            super().add(url_str)

import time
import threading
import configparser
import pathlib
class config_file(file):

    @staticmethod
    def read(file_path):
        # 相対パスを絶対パスへ変換
        file_path = pathlib.Path(file_path).resolve()
        if not os.path.exists(file_path) :
            raise ValueError("file is not exists. file_path=[{0}]".format(file_path))
        file_obj = open(file_path, "r", encoding='utf-8')
        return config_file(file_path, file_obj)

    def __init__(self, file_path, file_obj):
        super().__init__(file_path, file_obj)
        self.config = configparser.ConfigParser()
        self.config.read(file_path)
        # 最終内容更新日時を取得
        self.mtime = pathlib.Path(self.file_path).stat().st_mtime
        self.thread = threading.Thread(target=self.__reload__config__)
        self.thread.setDaemon(True)
        self.thread.start()

    def __reload__config__(self):
        while True:
            # 現在の設定ファイルのタイムスタンプを取得
            now_mtime = pathlib.Path(self.file_path).stat().st_mtime
            # 差が出た場合、設定ファイルを再読込
            if self.mtime != now_mtime :
                self.config.read(self.file_path)
                self.mtime = now_mtime
            # 5秒毎に監視
            time.sleep(5)

    def get(self, *keys):
        return self.config.get(*keys)
