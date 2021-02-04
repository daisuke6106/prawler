import os
from distutils.util import strtobool
from prawler import time
from prawler import prawler_repository
from prawler import history_file
from prawler import prawler_logger
from prawler import msg
from prawler import page
from prawler import config_file
# ===================================================================================================
# クラス郡定義
# ===================================================================================================
class page_iterator:

    @staticmethod
    def connect(url, func_get_timeout, index_selector, func_get_sleep_time, history, logger = None, connect_err_raise = False):
        start_page = page.connect( \
            url               = url, \
            timeout           = func_get_timeout(), \
            logger            = logger, \
            connect_err_raise = connect_err_raise\
        )
        return page_iterator( \
            start_page          = start_page, \
            func_get_timeout    = func_get_timeout, \
            index_selector      = index_selector, \
            func_get_sleep_time = func_get_sleep_time, \
            history             = history, \
            logger              = logger\
        )
    
    @staticmethod
    def init_by_accessed_page(start_page, func_get_timeout, index_selector, func_get_sleep_time, history, logger = None, connect_err_raise = False):
        return page_iterator( \
            start_page          = start_page, \
            func_get_timeout    = func_get_timeout, \
            index_selector      = index_selector, \
            func_get_sleep_time = func_get_sleep_time, \
            history             = history, \
            logger              = logger\
        )

    def __init__(self, start_page, func_get_timeout, index_selector, func_get_sleep_time, history, logger=None):
        if logger == None:
            logger = prawler_logger.get_instance()
        self.is_first            = True
        self.start_page          = start_page
        self.now_page            = start_page
        self.func_get_timeout    = func_get_timeout
        self.index_selector      = index_selector
        self.func_get_sleep_time = func_get_sleep_time
        self.history             = history
        self.logger              = logger

    def __iter__(self):
        return self
    
    def __next__(self):
        if self.is_first :
            self.is_first = False
            return self.start_page
        else :
            anchor_element_list  = self.now_page.get_element(self.index_selector).get_anchor()
            next_page            = None
            for anchor_element in anchor_element_list:
                # if self.history.is_visited(anchor_element.get_href()) :
                #     self.logger.info(msg("this next page url is visited. now_page=[{url}] nest_page_url=[{nest_page_url}]").param(url=self.now_page.url,nest_page_url=anchor_element.get_href()))
                # else:
                time.sleep(int(self.func_get_sleep_time()))
                next_page = page.connect(anchor_element.get_href(),  self.func_get_timeout(), self.logger)
                break
            if next_page is not None:
                self.now_page = next_page
                self.history.add(anchor_element.get_href())
                return next_page
            else:
                raise StopIteration()

# ===================================================================================================
# メイン
# ===================================================================================================
if __name__ == '__main__':

    #==================================================
    # カレントディレクトリをリポジトリのホームへ変更
    #==================================================
    os.chdir(os.path.dirname(os.path.abspath(__file__)) + "/../")

    #==================================================
    # リポジトリのセットアップ
    #==================================================
    repo = prawler_repository.setup("./")

    #==================================================
    # 設定ファイセットアップ
    #==================================================
    config_file = repo.config_file_obj
    
    #==================================================
    # ロガーのセットアップ
    #==================================================
    logger = repo.logger

    #==================================================
    # インデックスファイルのセットアップ
    #==================================================
    index_file = repo.index_file_obj

    #==================================================
    # 関数定義部
    #==================================================
    # タイムアウト時間を取得する関数
    def get_timeout():
        try:
            timeout = config_file.get("DEFAULT","READ_TIME_OUT")
            return int(timeout)
        except ValueError as e :
            logger.error(msg("An invalid value has been set for the parameter. timeout=[{timeout}]").param(timeout=timeout))
            raise e
    
    # スリープ時間を取得する関数
    def get_sleeptime():
        try:
            sleeptime = config_file.get("DEFAULT","SLEEP_TIME")
            return int(sleeptime)
        except ValueError as e :
            logger.error(msg("An invalid value has been set for the parameter. sleeptime=[{sleeptime}]").param(sleeptime=sleeptime))
            raise e
    
    # スタートページのURLを取得する関数
    def get_start_page_url():
        try:
            start_page_url = config_file.get("DEFAULT","START_PAGE_URL")
            return start_page_url
        except ValueError as e :
            logger.error(msg("An invalid value has been set for the parameter. start_page_url=[{start_page_url}]").param(start_page_url=start_page_url))
            raise e

    # インデックスページのURLが取得できる要素を選択するセレクター文字列を取得する関数
    def get_index_page_selector():
        try:
            index_page_selector = config_file.get("DEFAULT","INDEX_PAGE_SELECTOR")
            return index_page_selector
        except ValueError as e :
            logger.error(msg("An invalid value has been set for the parameter. index_page_selector=[{index_selector}]").param(index_page_selector=index_page_selector))
            raise e

    # データページのURLが取得できる要素を選択するセレクター文字列を取得する関数
    def get_data_page_selector():
        try:
            data_page_selector = config_file.get("DEFAULT","DATA_PAGE_SELECTOR")
            return data_page_selector
        except ValueError as e :
            logger.error(msg("An invalid value has been set for the parameter. data_page_selector=[{data_page_selector}]").param(data_page_selector=data_page_selector))
            raise e

    # データページのURLが取得できる要素を選択するセレクター文字列を取得する関数
    def get_save_again():
        try:
            save_again = config_file.get("DEFAULT","SAVE_AGAIN")
            return strtobool(save_again)
        except ValueError as e :
            logger.error(msg("An invalid value has been set for the parameter. save_again=[{save_again}]").param(save_again=save_again))
            raise e

    # インデックスをセットアップ
    history_indexpage = repo.setup_index_file("indexpage")
    
    # インデックスページに接続
    index_page_iterator = page_iterator.connect( \
        url                 = get_start_page_url(), \
        index_selector      = get_index_page_selector(), \
        func_get_timeout    = get_timeout, \
        func_get_sleep_time = get_sleeptime, \
        history             = history_indexpage, \
        logger              = logger, \
        connect_err_raise   = True \
    )
    # インデックスページを順繰りアクセス
    for index_page in index_page_iterator:

        # インデックスページから各データページのアンカーを取得する
        anchor_element_list  = index_page.get_element(get_data_page_selector()).get_anchor()

        # データページのアンカーを順繰りアクセス
        for anchor_element in anchor_element_list:

            # 設定として「すでに保存済みだった場合でも再度保存はしない（FALSE）」かつ、すでにアクセス済みだったら何もしない
            if not get_save_again() and repo.is_saved(anchor_element.get_href()) :
                logger.info(
                    msg("this next page url is visited.")
                    .detail(
                        next_page_url=anchor_element.get_href()
                    )
                )

            # 設定として「すでに保存済みだった場合でも再度保存する（TRUE）」もしくは、アクセスしていなかった場合、保存
            else:
                # アクセス前にサーバに負荷をかけないようスリープ
                time.sleep(int(get_sleeptime()))

                # 対象ページにアクセス
                next_page = page.connect(anchor_element.get_href(),  get_timeout(), logger)

                # リポジトリに保存
                repo.save(next_page)


