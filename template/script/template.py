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
                if self.history.is_visited(anchor_element.get_href()) :
                    self.logger.info(msg("this next page url is visited. now_page=[{url}] nest_page_url=[{nest_page_url}]").param(url=self.now_page.url,nest_page_url=anchor_element.get_href()))
                else:
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
    # 設定ファイル読み込み
    #==================================================
    config_file = config_file.read("../config/config.ini")
    
    #==================================================
    # リポジトリのセットアップ
    #==================================================
    repo = prawler_repository.setup("../")
    #==================================================
    # ロガーのセットアップ
    #==================================================
    logger = repo.logger
    #==================================================
    # 関数定義部
    #==================================================
    # 目的ページに達したときに実行する関数
    def visit_target_page_action(target_page):
        logger.info(msg("visit page. url=[{url}]").param(url=url))
    
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
            timeout = config_file.get("DEFAULT","SLEEP_TIME")
            return int(timeout)
        except ValueError as e :
            logger.error(msg("An invalid value has been set for the parameter. sleeptime=[{sleeptime}]").param(sleeptime=sleeptime))
            raise e
    
    # インデックスをセットアップ
    history_indexpage = history_file.setup("../history_indexpage")
    history_datapage  = history_file.setup("../history_datapage")
    
    # インデックスページに接続
    index_page_iterator = page_iterator.connect( \
        url                 = "###TARGET_URL###", \
        index_selector      = "###element selector###", \
        func_get_timeout    = get_timeout, \
        func_get_sleep_time = get_sleeptime, \
        history             = history_indexpage, \
        logger              = logger, \
        connect_err_raise   = True \
    )
    # インデックスページを順繰りアクセス
    for index_page in index_page_iterator:

        # インデックスページから各データページに順繰りアクセス
        data_page_iterator = page_iterator.init_by_accessed_page( \
            start_page          = index_page, \
            index_selector      = "###element selector###", \
            func_get_timeout    = get_timeout, \
            func_get_sleep_time = get_sleeptime, \
            history             = history_datapage, \
            logger              = logger, \
            connect_err_raise   = True \
        )

        # データページに順繰りアクセス
        for data_page in data_page_iterator:
            
            # リポジトリに保存
            repo.save(data_page)

