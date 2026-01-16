#coding: utf-8
from scrapy.spider import BaseSpider
from scrapy.selector import Selector
from Wechatproject.items import WechatprojectItem
from scrapy.http import Request


class WechatSpider(BaseSpider):
    """微信搜索程序 - Optimized version using Scrapy's built-in selectors"""
    name = "wechat"

    querystring = u"清华"
    type = 2  # 2-文章，1-微信号

    # Use list comprehension - more Pythonic
    start_urls = [
        "http://weixin.sogou.com/weixin?type=%d&query=%s&page=%d" % (type, querystring, i)
        for i in range(1, 50)
    ]

    def parse(self, response):
        """
        Parse search results using Scrapy's XPath selector (faster than BeautifulSoup).
        Scrapy's selectors are built on lxml which is significantly faster.
        """
        sel = Selector(response)
        sites = sel.xpath('//div[@class="txt-box"]/h4/a')

        for site in sites:
            item = WechatprojectItem()
            # Extract first element directly to avoid list handling later
            title_list = site.xpath("text()").extract()
            link_list = site.xpath("@href").extract()

            item["title"] = title_list[0] if title_list else ""
            item["link"] = link_list[0] if link_list else ""

            if item["link"]:
                yield Request(
                    url=item["link"],
                    meta={"item": item},
                    callback=self.parse2
                )

    def parse2(self, response):
        """Parse article content using Scrapy's XPath selector (faster than BeautifulSoup)"""
        sel = Selector(response)
        # Use XPath to extract all paragraph text at once
        content_parts = sel.xpath('//div[@class="rich_media_content" and @id="js_content"]//p//text()').extract()
        content = "".join(content_parts)

        item = response.meta['item']
        item["content"] = content
        return item
