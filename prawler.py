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
import argparse

from abc import ABCMeta, abstractmethod
from bs4 import BeautifulSoup
from urllib.parse import urljoin

# ===================================================================================================
class page:
    """
    単一のページを表すクラス

    任意のURLに接続して、HTMLのパーサ、DOM、保存などの機能を保有する。
    """

    @staticmethod
    def connect(url:str, timeout:int = 10, logger=None, connect_err_raise:bool = False):
        """ ページに接続する。
        
        引数にしていされたURLにアクセスする。

        Args:
            url(str):接続先URL
            timeout(int):接続時のタイムアウト設定値
            logger(prawler_logger):このクラスの処理で使用するロガー
            connect_err_raise(boolean):ページアクセスに失敗したときに例外を送出するかいなかのフラグ
        Raises:
            ValueError: 引数が不足しているもしくは、アクセスエラーが発生した場合
        Returns:
            page:URLのページインスタンス
        """
        if logger == None:
            logger = prawler_logger.get_instance()
        try:
            if url == None:
                raise ValueError("url is not set.")
            logger.info(msg("access start url=[{url}]").param(url=url))
            req_inst = requests.get(url=url, headers = {
                "accept"         : "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
                "accept-encoding": "gzip, deflate, br",
                "accept-language": "ja,en-US;q=0.9,en;q=0.8",
                "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.121 Safari/537.36"
                },timeout=timeout)
            logger.info(msg("connect success url=[{url}], status_code=[{status_code}]").param(url=url, status_code=req_inst.status_code))
            if (req_inst.status_code != 200):
                raise ValueError("bat status code. status_code=[{0}]".format(req_inst.status_code))
            headers  = dict(req_inst.headers)
            content  = req_inst.content
            # content_type = req_inst.headers['content-type']
            return page.create_page_instance(url, headers, content, logger)
        except Exception as e:
            logger.error(e)
            if connect_err_raise :
                raise e

    @staticmethod
    def read_latest(url:str, basedir:str, logger=None):
        """ 保存済みのもっとも新しいページ情報でページインスタンスを生成する。
        
        Args:
            url(str):読み込み対象のURL
            basedir(int):保存先のディレクトリパス（指定ディレクトリ直下にURLがハッシュ化されたディレクトリがある）
            logger(prawler_logger):このクラスの処理で使用するロガー
        Raises:
            ValueError: 引数が不足しているもしくは、アクセスエラーが発生した場合
        Returns:
            page:URLのページインスタンス
        """
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
    def read(url:str, dir:str, logger=None):
        """ 保存済みのページ情報でページインスタンスを生成する。
        
        Args:
            url(str):読み込み対象のURL
            basedir(int):保存先のディレクトリパス（指定ディレクトリ直下にcontentファイルなどがあるディレクトリを期待する。）
            logger(prawler_logger):このクラスの処理で使用するロガー
        Raises:
            ValueError: 引数が不足しているもしくは、アクセスエラーが発生した場合
        Returns:
            page:URLのページインスタンス
        """
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
    def url_to_hash(url:str) -> str:
        """ URLをハッシュ化（MD5）した文字列にして返却する。
        
        Args:
            url(str):対象のURL
        Returns:
            URL文字列をハッシュ化した文字列
        """
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
    def create_page_instance(url:str, header:dict, content:str, logger:"prawler_logger")->"page":
        """ 引数に指定された情報をもとにページのインスタンスを生成する。

        クラスはヘッダに指定されている「content-type」をもとに決定される。

        Args:
            url(str):URL
            header(dict):レスポンスヘッダ
            logger(prawler_logger):このクラスの処理で使用するロガー
        Returns:
            page:URLのページインスタンス
        """
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

    def save(self, basedir) -> None:
        """ このページを引数に指定された場所に保存する。

        引数に指定されたディレクトリ直下に「URLをハッシュ化したディレクトリ名」を作成、
        さらにその下に現在日時（YYYYMMDDHHMMSS）のディレクトリを作成し、そのディレクトリ配下に
        レスポンスヘッダ、ページ本体などが作成される。

        Args:
            url(str):URL
            header(dict):レスポンスヘッダ
            logger(prawler_logger):このクラスの処理で使用するロガー
        Returns:
            page:URLのページインスタンス
        """
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


class html_page(page):
    """
    単一のHTMLページを表すクラス

    任意のURLに接続して、HTMLのパーサ、DOM、保存などの機能を保有する。
    """
    def __init__(self, url, header, content, logger):
        super().__init__(url = url, header = header, content = content, logger = logger)
        self.soup = BeautifulSoup(self.content, "html.parser")

    def get_title(self) -> str:
        """ このページのタイトルを取得し、返却する。

        Returns:
            str:このページのタイトル
        """
        return self.soup.find("title").get_text()

    def get_element(self, selector:str) -> "element_list":
        """ 引数に指定された要素を取得し、返却する。

        参考:https://qiita.com/Chanmoro/items/db51658b073acddea4ac
             https://www.pynote.info/entry/beautiful-soup-find-elements
             https://python.civic-apps.com/beautifulsoup4-selector/
             http://python.zombie-hunting-club.com/entry/2017/11/08/192731

        Args:
            selector(str):取得対象の要素。例：div配下のp2クラスを取得する場合、"div > .p2"
            header(dict):レスポンスヘッダ
            logger(prawler_logger):このクラスの処理で使用するロガー
        Returns:
            page:URLのページインスタンス
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
        return element_list_result

# ===================================================================================================
class element_list:
    """
    HTMLの複数の要素の要素を表すクラス

    HTMLのページに対して、DOM操作を行い、要素の一覧を取得するような場合、このクラスの単一のインスタンスが返却される。
    このインスタンスはfor文で１要素ずつ取り出せることができる。
    """
    def __init__(self, page, bs_element_list):
        self.page = page
        self.element_list = list()
        if bs_element_list != None :
            for bs_element in bs_element_list:
                self.element_list.append( self.__create_element( page, bs_element ) )

    def content(self) -> str:
        """
        要素の内容を単一の文字列にして返却する。

        この要素一覧が持つ要素の内容を単一の文字に結合して返却する。

        Returns:
            str:要素の内容
        """
        content = ""
        for element in self.element_list:
            content += element.content()
        return content

    def get_anchor(self) -> "element_list":
        """
        このインスタンスが持つ要素からアンカーの一覧を抽出し、新たな要素一覧として返却する。

        なお、返却されるアンカーの一覧は以下の内容が除外される。
        ①href属性が空
        ②重複しているhrefを持つ要素

        Returns:
            str:要素の内容
        """
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
        return return_element_lsit
    
    def __has_same_anchor(self, appended_anchor_list, check_target_anchor):
        for appended_anchor in appended_anchor_list:
            if appended_anchor.get_href() == check_target_anchor.get_href():
                return True
        return False

    def print_href(self):
        """
        このインスタンスが持つ要素からアンカーの一覧を抽出し、標準出力に出力する。

        なお、返却されるアンカーの一覧は以下の内容が除外される。
        ①href属性が空
        ②重複しているhrefを持つ要素

        """
        for element in self.get_anchor().element_list:
            href = element.get_href()
            if href != None and href != "":
                print ( href )

    def __create_element(self, page, bs_element):
        if bs_element.name == "a":
            return anchor_html_element(page, bs_element)
        else:
            return html_element(page, bs_element)

    def __iter__(self):
        self.__iterator_count = 0
        return self
    
    def __next__(self) -> "html_element":
        if self.__iterator_count == len(self.element_list) :
            raise StopIteration()
        return_element = self.element_list[self.__iterator_count]
        self.__iterator_count += 1
        return return_element

# ===================================================================================================
class html_element:
    """
    HTMLの単一の要素を表すクラス

    element_listのインスタンスで単一の要素を取り出した場合、本クラスのインスタンスが返却される。
    このクラスは１つの要素に対する属性、内容の取得、アンカーの一覧の取得などの機能を持つ。
    
    """
    def __init__(self, page, bs_element):
        self.page       = page
        self.bs_element = bs_element

    def get_attr(self, attr) -> str:
        """
        この要素がもつ属性値を文字列として返却する。

        Returns:
            str:属性値
        """
        return self.bs_element[attr]

    def content(self) -> str:
        """
        この要素がもつ内容を文字列として返却する。

        Returns:
            str:要素の内容
        """
        return self.bs_element.get_text()

    def get_anchor(self) -> element_list:
        """
        この要素からアンカーを検索して、要素の一覧を表す単一のインスタンスを返却する。

        Returns:
            element_list:アンカー一覧
        """
        anchor_bs_element_list = self.bs_element.find_all("a")
        return element_list(self.page, anchor_bs_element_list)

    def __str__(self):
        return self.bs_element.prettify().replace("\n","")

# ===================================================================================================
class anchor_html_element(html_element):
    """
    HTMLの単一のアンカー要素を表すクラス

    element_listのインスタンスで単一の要素を取り出した場合、アンカーの要素だった場合、本クラスのインスタンスが返却される。
    get_hrefで要素の「href」属性を取り出した場合、リンク先が相対パスであった場合、絶対パスへ補完されて返却される。
    
    """
    def __init__(self, page, bs_element):
        super().__init__(page, bs_element)

    def get_href(self) -> str:
        """
        この要素がもつhrefの属性値を文字列として返却する。
        なお、リンク先が相対パスであった場合、絶対パスへ補完されて返却される。

        Returns:
            str:要素の内容
        """
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
#####################################################################################################
# 
#####################################################################################################
class msg:
    """
    ログに出力する際に使用するメッセージを表すクラス。

    以下のように設定。
    "connect success url=[{url}], status_code=[{status_code}]")
            .param(url=url, status_code=req_inst.status_code)
            .detail(
                selector = selector,
                element_list = [str(element) for element in element_list_result]),
            )

    それをそのまま出力（__str__を介して）すると以下のようJSON形式で出力される。
    {"body": "connect success url=[http://aaa.con], status_code=[200]", "selector": ".pager", "element_list": ["a","table"]}
    """
    def __init__(self, message ):
        self.message    = message
        self.param_dict = None
        self.detail_data = None
    
    def param(self, **param_dict):
        """
        メッセージ本文の埋め文字を設定する。

        Examples:
            .param(url=url, status_code=req_inst.status_code)
        Args:
            param_dict(dict):メッセージ本文の埋め文字
        """
        self.param_dict = param_dict
        return self
    
    def detail(self, **detail_data):
        """
        このメッセージに付随する情報をディクショナリ形式で設定する。

        Examples:
            .detail(
                selector = selector,
                element_list = [str(element) for element in element_list_result]),
            )
        Args:
            detail_data(dict):このメッセージに付随する情報
        """
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

class abstract_prawler_logger(metaclass=ABCMeta):
    """
        ロギングの抽象クラス
    """

    @abstractmethod
    def debug(self, msg:msg):
        pass

    @abstractmethod
    def info(self, msg:msg):
        """
        INFOレベルでのメッセージを出力する。

        Examples:
            .detail(
                selector = selector,
                element_list = [str(element) for element in element_list_result]),
            )
        Args:
            detail_data(dict):このメッセージに付随する情報
        """
        pass

    @abstractmethod
    def warning(self, e):
        pass

    @abstractmethod
    def error(self, e):
        pass

    @abstractmethod
    def add_file_log_handler(self, file_path):
        pass

class prawler_logger_nonlog(abstract_prawler_logger):

    @classmethod
    def get_instance(cls):
        if not hasattr(cls, "_instance") :
            cls._instance = prawler_logger_nonlog()
        return cls._instance

    def debug(self, msg):
        pass

    def info(self, msg):
        pass

    def warning(self, e):
        pass

    def error(self, e):
        pass

    def add_file_log_handler(self, file_path):
        pass


class prawler_logger(abstract_prawler_logger):

    @classmethod
    def get_instance(cls):
        if not hasattr(cls, "_instance") :
            cls._instance = prawler_logger()
        return cls._instance

    def __init__(self):
        # https://docs.python.org/ja/3/library/logging.html#logrecord-attributes
        self.logger = getLogger(__name__)
        self.fotmatter = Formatter(fmt='{"timestamp":"%(asctime)s","process":"%(process)d","level":"%(levelname)s","message":%(message)s}', datefmt='%Y/%m/%d-%H:%M:%S')

        # stream_handler = StreamHandler()
        # stream_handler.setLevel(DEBUG)
        # stream_handler.setFormatter(self.fotmatter)
        # self.logger.addHandler(stream_handler)
        self.logger.setLevel(DEBUG)
        self.logger.propagate = False
    
    def add_console_log_handler(self):
        stream_handler = StreamHandler()
        stream_handler.setLevel(DEBUG)
        stream_handler.setFormatter(self.fotmatter)
        self.logger.addHandler(stream_handler)

    def add_file_log_handler(self, file_path):
        file_handler = FileHandler(file_path)
        file_handler.setLevel(DEBUG)
        file_handler.setFormatter(self.fotmatter)
        self.logger.addHandler(file_handler)

    def debug(self, msg):
        self.logger.debug(str(msg))
    
    def info(self, msg):
        self.logger.info(str(msg))
    
    def warning(self, msg):
        self.logger.warning(str(msg))

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
        return page.read_latest(url, basedir=self.data_path, logger=self.logger)

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

# ===================================================================================================
# メイン
# ===================================================================================================
if __name__ == '__main__':

    #==================================================
    # カレントディレクトリをリポジトリのホームへ変更
    #==================================================
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    #==================================================
    # コマンド引数
    # 参考：https://qiita.com/kzkadc/items/e4fc7bc9c003de1eb6d0
    #==================================================
    argpaese = argparse.ArgumentParser(description="スクレイピングを行うためのリポジトリを所定のディレクトリに作成する。")
    # 必須オプション
    argpaese.add_argument("dir", help="リポジトリの作成先")
    # 引数を解析
    args = argpaese.parse_args()
    # 引数を取得
    dir = args.dir
    # リポジトリを作成する。
    prawler_repository.init(dir)
    