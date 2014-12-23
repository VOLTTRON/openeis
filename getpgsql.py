
import html.parser
import platform
import re
import threading
import urllib.parse
import urllib.request


PSQL_BINARY_DOWNLOAD_URL = ('http://www.enterprisedb.com/'
                            'products-services-training/pgbindownload')
PSQL_BINARY_DOWNLOAD_RE = re.compile(
    r'^/postgresql-[0-9-]+-binaries-(\w+)(?:\?.*)?$')
SYSTEMS = ['linux32', 'linux64', 'osx', 'windows32', 'windows64']


def get_download_url(front_url):
    cookie_handler = urllib.request.HTTPCookieProcessor()
    opener = urllib.request.build_opener(cookie_handler)
    request = urllib.request.Request(front_url, method='HEAD')
    response = opener.open(request)
    assert response.status == 200
    for cookie in cookie_handler.cookiejar:
        if cookie.name == 'downloadFile':
            return urllib.parse.unquote(cookie.value)


def get_front_urls(url=PSQL_BINARY_DOWNLOAD_URL, system=None):
    if system is None:
        system = platform.system().lower()
        if system == 'macos':
            system = 'osx'
        else:
            system += platform.architecture()[0][:2]
    if system not in SYSTEMS:
        raise ValueError('system must be one of {}; got {}'.format(
            ', '.join(SYSTEMS), system))
    links = []
    class LinkParser(html.parser.HTMLParser):
        def handle_starttag(self, tag, attrs):
            if tag == 'a':
                for name, value in attrs:
                    if name == 'href':
                        match = PSQL_BINARY_DOWNLOAD_RE.match(value)
                        if match and match.group(1).lower() == system:
                            links.append(value)
                        break
    parser = LinkParser()
    with urllib.request.urlopen(url) as response:
        parser.feed(response.read().decode('utf-8'))
    parts = urllib.parse.urlsplit(url)
    for i, link in enumerate(links):
        links[i] = urllib.parse.urlunsplit(
            parts[:2] + urllib.parse.urlsplit(link)[2:])
    return links


def get_download_urls(front_urls, threadcount=None):
    front_urls = list(enumerate(front_urls))
    if not threadcount:
        threadcount = len(front_urls)
    download_urls = []
    def fetch_url():
        while True:
            try:
                index, url = front_urls.pop()
            except IndexError:
                return
            download_urls.append((index, get_download_url(url)))
    threads = []
    for i in range(threadcount):
        thread = threading.Thread(target=fetch_url, daemon=True)
        thread.start()
        threads.append(thread)
    for thread in threads:
        thread.join()
    download_urls.sort()
    return [url for i, url in download_urls]


if __name__ == '__main__':
    url = 'http://www.enterprisedb.com/postgresql-940-binaries-linux32?ls=Crossover&amp;type=Crossover'
    pgfile = 'file:///home/brandon/devel/postgres/pgdownloads.html'
    #print(get_download_url(url))
    links = get_front_urls()
    print('\n'.join(links))
    dlinks = get_download_urls(links)
    print('\n'.join(dlinks))
    #for link in links:
    #    print(get_download_url(link))
