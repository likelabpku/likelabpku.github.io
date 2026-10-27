"""Build the Chinese edition from the current English pages (Python stdlib only).

English HTML is the source of truth; i18n/zh-CN.json contains translations.
Run this after editing an English page or the shared CSS/JavaScript.
"""
from hashlib import sha256
from html import escape, unescape
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit
import json
import re

ROOT = Path(__file__).resolve().parents[1]
PAGES = ('index.html', 'news.html', 'people.html', 'publications.html', 'contact.html')
CATALOG = json.loads((ROOT / 'i18n/zh-CN.json').read_text(encoding='utf-8'))
STRINGS = CATALOG['strings']
NAMES = CATALOG['names']
VOID = set('area base br col embed hr img input link meta param source track wbr'.split())


def translate(text):
    value = text.strip()
    translated = STRINGS.get(value, NAMES.get(value))
    if translated is None:
        if value.endswith(' · LIKE Lab · Peking University'):
            translated = translate(value.split(' · ')[0]) + ' · LIKE Lab · 北京大学'
        elif value.startswith('Read paper: '):
            translated = '阅读论文：' + value.removeprefix('Read paper: ')
        elif ' — ' in value:
            translated = ' — '.join(translate(part) for part in value.split(' — '))
        elif m := re.fullmatch(r'(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec) (\d{4})', value):
            month = 'Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec'.split().index(m[1]) + 1
            translated = f'{m[2]}年{month}月'
        elif m := re.fullmatch(r'(\d+) updates', value):
            translated = f'{m[1]} 条动态'
        elif m := re.fullmatch(r'(\d+) papers?', value):
            translated = f'{m[1]} 篇论文'
        elif m := re.fullmatch(r'View (\d+) papers', value):
            translated = f'查看 {m[1]} 篇论文'
        elif m := re.fullmatch(r'Source (\d+)', value):
            translated = f'来源 {m[1]}'
        elif m := re.fullmatch(r'(\d+) publications', value):
            translated = f'共 {m[1]} 篇论文'
        elif m := re.fullmatch(r'(\d+) of (\d+)', value):
            translated = f'第 {m[1]} 张，共 {m[2]} 张'
        elif m := re.fullmatch(r'Show photo (\d+) of (\d+): (.+)', value):
            translated = f'查看第 {m[1]} 张照片（共 {m[2]} 张）：{translate(m[3])}'
        elif ' · ' in value:
            translated = ' · '.join(translate(part) for part in value.split(' · '))
        else:
            return text
    return text[:len(text) - len(text.lstrip())] + translated + text[len(text.rstrip()):]


class ChinesePage(HTMLParser):
    def __init__(self, filename):
        super().__init__(convert_charrefs=True)
        self.filename = filename
        self.stack = []
        self.output = []

    def handle_starttag(self, tag, attrs):
        self.start(tag, attrs, False)

    def handle_startendtag(self, tag, attrs):
        self.start(tag, attrs, True)

    def start(self, tag, attrs, self_closing):
        original = dict(attrs)
        classes = set(original.get('class', '').split())
        ancestors = set().union(*(item['classes'] for item in self.stack))
        inherited_frozen = self.stack and self.stack[-1]['frozen']
        # Keep scholarly titles, abstracts, and author spellings in their original language.
        frozen = bool(inherited_frozen or 'pub-authors' in classes or 'news-paper-author' in classes
                      or (tag == 'h3' and ancestors & {'pub-item', 'highlight'})
                      or (tag == 'p' and 'pub-item' in ancestors and self.stack[-1]['tag'] == 'details')
                      or (tag == 'a' and 'news-papers' in ancestors
                          and any(item['tag'] == 'ul' for item in self.stack)))
        switch = 'data-language-switch' in original
        values = []
        for key, value in attrs:
            if value is None:
                values.append(key)
                continue
            if tag == 'html' and key == 'lang':
                value = 'zh-CN'
            elif switch and key in ('href', 'lang', 'hreflang', 'aria-label'):
                value = {'href': '../' + self.filename, 'lang': 'en', 'hreflang': 'en',
                         'aria-label': 'Switch to English'}[key]
            elif tag == 'link' and original.get('rel') == 'alternate' and key == 'href':
                value = self.filename if original.get('hreflang') == 'zh-CN' else '../' + self.filename
            elif key in ('href', 'src') and not urlsplit(value).scheme and not value.startswith(('#', '/', '?')):
                # Page navigation remains within zh/; media and bibliography share the root assets.
                if value.startswith(('assets/', 'data/')):
                    value = '../' + value
            elif key in ('alt', 'title', 'placeholder', 'aria-label', 'aria-roledescription'):
                value = translate(value)
            elif tag == 'meta' and original.get('name') == 'description' and key == 'content':
                value = translate(value)
            values.append(f'{key}="{escape(value, quote=True)}"')
        self.output.append('<' + tag + (' ' if values else '') + ' '.join(values)
                           + ('/>' if self_closing else '>'))
        if tag not in VOID and not self_closing:
            self.stack.append({'tag': tag, 'classes': classes, 'frozen': frozen, 'switch': switch})

    def handle_endtag(self, tag):
        self.output.append(f'</{tag}>')
        if self.stack and self.stack[-1]['tag'] == tag:
            self.stack.pop()

    def handle_data(self, data):
        current = self.stack[-1] if self.stack else {}
        if current.get('tag') in ('script', 'style'):
            self.output.append(data)
        elif current.get('switch'):
            self.output.append('EN')
        else:
            self.output.append(escape(data if current.get('frozen') else translate(data), quote=False))

    def handle_decl(self, decl):
        self.output.append(f'<!{decl}>')

    def handle_comment(self, data):
        self.output.append(f'<!--{data}-->')


def prepare_english(source, filename):
    for marker in ('language-switch', 'language-alternates'):
        source = re.sub(rf'<!-- {marker}:start -->.*?<!-- {marker}:end -->', '', source, flags=re.S)
    switch = (f'<!-- language-switch:start --><a class="language-switch" data-language-switch '
              f'href="zh/{filename}" lang="zh-CN" hreflang="zh-CN" '
              'aria-label="切换到中文版">中文</a><!-- language-switch:end -->')
    if '<button class="menu-toggle"' not in source:
        raise ValueError(f'{filename}: missing navigation insertion point')
    source = source.replace('<button class="menu-toggle"', switch + '<button class="menu-toggle"', 1)
    alternates = (f'<!-- language-alternates:start -->'
                  f'<link rel="alternate" hreflang="en" href="{filename}">'
                  f'<link rel="alternate" hreflang="zh-CN" href="zh/{filename}">'
                  '<!-- language-alternates:end -->')
    source = source.replace('</head>', alternates + '</head>', 1)
    for asset in ('site.css', 'site.js'):
        digest = sha256((ROOT / 'assets' / asset).read_bytes()).hexdigest()[:12]
        source = re.sub(rf'assets/{re.escape(asset)}(?:\?v=[a-zA-Z0-9]+)?',
                        f'assets/{asset}?v={digest}', source)
    # Search accepts both original author spellings and verified Chinese names in either edition.
    def search_aliases(match):
        value = unescape(match[1])
        for english, chinese in NAMES.items():
            if re.search(r'\b' + re.escape(english.lower()) + r'\b', value) and chinese not in value:
                value += ' ' + chinese
        return 'data-search="' + escape(value, quote=True) + '"'
    source = re.sub(r'data-search="([^"]*)"', search_aliases, source)
    return source


def build():
    outputs = {}
    for filename in PAGES:
        source = prepare_english((ROOT / filename).read_text(encoding='utf-8'), filename)
        parser = ChinesePage(filename)
        parser.feed(source)
        parser.close()
        chinese = ''.join(parser.output)
        # GA4 belongs to each page, including both language editions.
        for html in (source, chinese):
            if html.count("gtag('config', 'G-2CBV6S0XQP')") != 1:
                raise ValueError(f'{filename}: expected exactly one GA4 configuration')
        outputs[ROOT / filename] = source
        outputs[ROOT / 'zh' / filename] = chinese
    (ROOT / 'zh').mkdir(exist_ok=True)
    for path, html in outputs.items():
        if not path.exists() or path.read_text(encoding='utf-8') != html:
            path.write_text(html, encoding='utf-8')
    print('Built 5 English and 5 Chinese pages; shared assets and GA4 retained.')


if __name__ == '__main__':
    build()
