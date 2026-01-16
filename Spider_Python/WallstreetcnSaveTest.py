#!/usr/bin/env python
# -*- coding:utf-8 -*-

import sys
import re
import urllib, urllib2
import requests
import pymongo
import datetime
import multiprocessing as mp

# Pre-compile regex pattern for better performance
CONTENT_PATTERN = re.compile(r'"type":"(.*?)","codeType".*?"contentHtml":"(.*?)","data".*?"categorySet":"(.*?)","hasMore"')

# Use a requests session for connection pooling
session = requests.Session()

Category_Map = {
    "1":u"外汇",
    "2":u"股市",
    "3":u"商品",
    "4":u"债市",
    "5":u"央行",
    "9":u"中国",
    "10":u"美国",
    "11":u"欧元区",
    "12":u"日本",
    "13":u"英国",
    "14":u"澳洲",
    "15":u"加拿大",
    "16":u"瑞士",
    "17":u"其他地区"
}
def num2name(category_num):
    return Category_Map.get(category_num, "")

# Connection pool for MongoDB - reuse connections across processes
_mongo_connections = {}

class MongoDBIO:
    # 申明相关的属性
    def __init__(self, host, port, name, password, database, collection):
        self.host = host
        self.port = port
        self.name = name
        self.password = password
        self.database = database
        self.collection = collection

    # 连接数据库，db和posts为数据库和集合的游标
    def Connection(self):
        # Use connection pooling - cache connections by host:port:database
        conn_key = (self.host, self.port, self.database)
        if conn_key not in _mongo_connections:
            # Use MongoClient instead of deprecated Connection
            _mongo_connections[conn_key] = pymongo.MongoClient(host=self.host, port=self.port)
        connection = _mongo_connections[conn_key]
        db = connection[self.database]
        if self.name or self.password:
            db.authenticate(name=self.name, password=self.password)
        posts = db[self.collection]
        return posts

def ResultSave(save_host, save_port, save_name, save_password, save_database, save_collection, save_content):
    posts = MongoDBIO(save_host, save_port, save_name, save_password, save_database, save_collection).Connection()
    posts.save(save_content)

def ResultSaveBatch(save_host, save_port, save_name, save_password, save_database, save_collection, save_contents):
    """Batch insert for better performance"""
    if not save_contents:
        return
    posts = MongoDBIO(save_host, save_port, save_name, save_password, save_database, save_collection).Connection()
    posts.insert_many(save_contents)

def Spider(url, data):
    # Use session for connection pooling (HTTP keep-alive)
    content = session.get(url=url, params=data).content
    return content

# Pre-define category sets for faster lookup
DISTRICT_CATEGORIES = frozenset([u"中国", u"美国", u"欧元区", u"日本", u"英国", u"澳洲", u"加拿大", u"瑞士", u"其他地区"])
PROPERTY_CATEGORIES = frozenset([u"外汇", u"股市", u"商品", u"债市"])
CENTRALBANK_CATEGORIES = frozenset([u"央行"])

def ContentSave(item):
    # 保存配置
    save_host = "localhost"
    save_port = 27017
    save_name = ""
    save_password = ""
    save_database = "textclassify"
    save_collection = "WallstreetcnSave"

    source = "wallstreetcn"
    createdtime = datetime.datetime.now()
    type = item[0]
    content = item[1].decode("unicode_escape").encode("utf-8")

    # district的筛选 - use pre-defined frozensets for faster intersection
    categorySet = item[2]
    category_num = categorySet.split(",")
    category_name = set(map(num2name, category_num))

    district = ",".join(category_name & DISTRICT_CATEGORIES)
    property = ",".join(category_name & PROPERTY_CATEGORIES)
    centralbank = ",".join(category_name & CENTRALBANK_CATEGORIES)

    save_content = {
        "source":source,
        "createdtime":createdtime,
        "content":content,
        "type":type,
        "district":district,
        "property":property,
        "centralbank":centralbank
    }
    ResultSave(save_host, save_port, save_name, save_password, save_database, save_collection, save_content)

def func(page):
    url = "http://api.wallstreetcn.com/v2/livenews"
    data = {"page": page}
    content = Spider(url, data)
    # Use pre-compiled regex pattern
    items = CONTENT_PATTERN.findall(content)
    if len(items) == 0:
        print "The End Page:", page
        data = urllib.urlencode(data)
        full_url = url + '?' + data
        print full_url
        sys.exit(0)
    else:
        print "The Page:", page, "Downloading..."
        for item in items:
            ContentSave(item)


if __name__ == '__main__':

    start = datetime.datetime.now()

    start_page = 1
    end_page = 3300

    # 多进程抓取 - use optimal number of workers based on CPU cores
    pages = range(start_page, end_page)  # Use range directly instead of list comprehension
    p = mp.Pool(processes=mp.cpu_count())  # Explicitly set pool size
    p.map_async(func, pages)
    p.close()
    p.join()

    # 单进程抓取
    url = "http://api.wallstreetcn.com/v2/livenews"
    page = end_page

    while True:
        data = {"page": page}
        content = Spider(url, data)
        # Use pre-compiled regex pattern
        items = CONTENT_PATTERN.findall(content)
        if len(items) == 0:
            print "The End Page:", page
            data = urllib.urlencode(data)
            full_url = url + '?' + data
            print full_url
            break
        else:
            print "The Page:", page, "Downloading..."
            for item in items:
                ContentSave(item)
            page += 1

    end = datetime.datetime.now()
    print "last time: ", end - start
