#!/bin/bash
PRAWLER_HOME="$(dirname ${0})"
export PYTHONPATH="${PRAWLER_HOME}:$PYTHONPATH"
if [ $# = 0 ]; then
    echo "usage: prawler <command> [<args>]"
    echo "command"
    echo "  inter         :インタラクティブモードにて開きます。"
    echo "  print_href    :指定されたURLにアクセスし、所定の要素配下に存在するアンカーからURLを標準出力へ出力する。"
fi
if [ "${1}" = "inter" ]; then
python -i -c "
from prawler import prawler
from prawler import page
print('--------------------------------------------------');
print('prawler');
print('--------------------------------------------------');
print('Usage:');
print('ページを開く');
print('page = page.connect(\"http://gigazine.net\")');
print('開いたページから要素の一覧を取得');
print('element_list = page.get_element(\"div.content section div.card h2 span\")');
"
fi
if [ "${1}" = "print_href" ]; then
python -c "
from prawler import prawler
from prawler import page
page.connect('${2}').get_element('${3}').print_href()
"
fi
if [ "${1}" = "save" ]; then
python -c "
from prawler import prawler
from prawler import page
page.connect('${2}').save('${3}')
"
fi