import requests

Proxy = 'socks5://vscyrquo:k6xdndmuz1mr@185.72.242.164:5847'
proxies = {'http': Proxy, 'https': Proxy}
url = 'https://httpbin.org/ip'
_a = requests.get(url, proxies=proxies)
_b = requests.get(url)
print(_a.text)
print(_b.text)