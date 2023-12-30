import sys
import clipboard
import markdown
from bs4 import BeautifulSoup as bs4

if __name__ == '__main__':

    md = clipboard.paste()
    lines = md.splitlines()
    html = ""
    for line in lines:
        sharp_list = line.split(' ')
        if '##' in sharp_list:
            html += ('<hr contenteditable="false" data-ke-type="horizontalRule" data-ke-style="style5" />' + '\n')
            html += (line + '\n')
        else:
            html += (line + '\n')
    html = markdown.markdown(html, extensions=['fenced_code', 'nl2br', 'tables'])
    html = bs4(html, "html.parser")
    for tag in html.find_all('table'):
        tag['table-type'] = 'table'
    clipboard.copy(str(html))
