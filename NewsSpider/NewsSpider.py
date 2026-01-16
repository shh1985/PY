# -*- coding: utf-8 -*-
import os
import requests
from lxml import etree

# Pre-compile regex pattern for better performance
import re
PAGE_INFO_PATTERN = re.compile(
    r'<div class="titleBar" id=".*?"><h2>(.*?)</h2><div class="more"><a href="(.*?)">.*?</a></div></div>',
    re.S
)

# Use a requests session for HTTP connection pooling (keep-alive)
session = requests.Session()


def StringListSave(save_path, filename, slist):
    if not os.path.exists(save_path):
        os.makedirs(save_path)
    path = os.path.join(save_path, filename + ".txt")
    with open(path, "w") as fp:
        for s in slist:
            fp.write("%s\t\t%s\n" % (s[0].encode("utf8"), s[1].encode("utf8")))


def Page_Info(myPage):
    """Extract page info using pre-compiled regex"""
    return PAGE_INFO_PATTERN.findall(myPage)


def New_Page_Info(new_page):
    """Extract new page info using XPath (faster than regex for HTML parsing)"""
    dom = etree.HTML(new_page)
    new_items = dom.xpath('//tr/td/a/text()')
    new_urls = dom.xpath('//tr/td/a/@href')
    return zip(new_items, new_urls)


def Spider(url):
    print "downloading ", url
    # Use session for connection reuse
    myPage = session.get(url).content.decode("gbk")
    myPageResults = Page_Info(myPage)

    save_path = u"网易新闻抓取"
    StringListSave(save_path, "0_" + u"新闻排行榜", myPageResults)

    for i, (item, page_url) in enumerate(myPageResults, start=1):
        print "downloading ", page_url
        # Reuse session connection
        new_page = session.get(page_url).content.decode("gbk")
        newPageResults = New_Page_Info(new_page)
        filename = str(i) + "_" + item
        StringListSave(save_path, filename, newPageResults)


if __name__ == '__main__':
    print "start"
    start_url = "http://news.163.com/rank/"
    Spider(start_url)
    print "end"