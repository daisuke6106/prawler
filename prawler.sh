#!/bin/bash
PRAWLER_HOME="$(dirname ${0})"
export PYTHONPATH="${PRAWLER_HOME}:$PYTHONPATH"
python -i -c "
from prawler import page
print('--------------------------------------------------');
print('prawler');
print('--------------------------------------------------');
print('Usage:');
print('ページを開く');
print('page = page.connect(\"http://gigazine.net\")');
print('開いたページから要素の一覧を取得');
print('element_list = page.get_element(\"div.content section div.card h2 span\")');
print('要素を画面に表示');
print('element_list.roop(print_content)');
"