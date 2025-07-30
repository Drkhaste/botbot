import json
import re
import string
import random

def read_file(file_name):
    with open(file_name, 'r', encoding='UTF-8') as f:
        Lines = f.readlines()
    return Lines

def extract_proxy_info(proxy_string):
    pattern = re.compile(r'socks5://(.*?):(.*?)@(.*?):(\d+)')
    match = pattern.match(proxy_string)
    if match:
        username, password, ip, port = match.groups()
        return ip, int(port), username, password
    else:
        return None

def generate_hash(length):
    characters = string.ascii_letters + string.digits
    return ''.join(random.choices(characters, k=length))

def normalize_link(text):
    if text[0] == '@':
        return text
    else:
        try:
            if 'joinchat' in text:
                pattern = r'https\:\/\/t\.me\/joinchat\/'
                hash_text = re.sub(pattern, '', text)
                return hash_text
            else:
                pattern = r'https\:\/\/t\.me\/\+'
                hash_text = re.sub(pattern, '', text)
                return hash_text
        except:
            return "Invalid"

def array_chunk(lst, size):
    out = []
    count = 0
    T = []
    for i in lst:
        T.append(i)
        count += 1
        if count == size:
            count = 0
            out.append(T)
            T = []
    else:
        out.append(T)
    return out

async def rTFetch(dbc, name, ifc=''):
    async with dbc.cursor() as cursor:
        query = f'SELECT * FROM {name} {ifc} ORDER BY RAND() LIMIT 1'
        await cursor.execute(query)
        result = await cursor.fetchall()
        if cursor.rowcount > 0:
            return result[0]
        else:
            return None
