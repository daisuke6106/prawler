# -*- coding: utf-8 -*-
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

class html_page:

    def __init__(self, url, timeout=10):
        self.url = url
        self.timeout = timeout
        self.req = requests.get(url=self.url, timeout=self.timeout)
        self.soup = BeautifulSoup(self.req.content, "html.parser")

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

class html_element:

    def __init__(self, page, bs_element):
        self.page       = page
        self.bs_element = bs_element

    def content(self):
        return self.bs_element.get_text()

class anchor_html_element(html_element):

    def __init__(self, page, bs_element):
        super().__init__(page, bs_element)

    def get_href(self):
        href = self.bs_element["href"]
        if href != "" :
            return urljoin(self.page.url, href)
        return None

page = html_page("http://gigazine.net")
element_list = page.get_element("div.content section div.card h2 span")

def print_content(element):
    print ( element.content() )

element_list.roop(print_content)
print(element_list)

