#!/usr/bin/env python
# -*- coding:utf-8 -*-

import os
import time
import datetime
import codecs
import multiprocessing as mp
from selenium import webdriver
from selenium.webdriver.common.proxy import *
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

site = 'http://flight.qunar.com'
hot_city_list = [u'上海', u'北京', u'广州', u'深圳']
num = len(hot_city_list)

# Create ticket directory once at module load
TICKET_DIR = u'./ticket/'
if not os.path.exists(TICKET_DIR):
    os.makedirs(TICKET_DIR)


def one_driver_ticket(driver, from_city, to_city):
    date = datetime.date.today()
    tomorrow = date + datetime.timedelta(days=1)
    tomorrow_string = tomorrow.strftime('%Y-%m-%d')

    # Use explicit waits instead of fixed sleep times for better performance
    wait = WebDriverWait(driver, 10)

    from_city_elem = driver.find_element_by_name('fromCity')
    from_city_elem.clear()
    from_city_elem.send_keys(from_city)

    to_city_elem = driver.find_element_by_name('toCity')
    to_city_elem.clear()
    to_city_elem.send_keys(to_city)

    from_date_elem = driver.find_element_by_name('fromDate')
    from_date_elem.clear()
    from_date_elem.send_keys(tomorrow_string)

    driver.find_element_by_xpath('//button[@type="submit"]').click()

    # Wait for page to load instead of fixed sleep
    try:
        wait.until(EC.presence_of_element_located((By.XPATH, "//*")))
    except:
        time.sleep(5)  # Fallback to fixed sleep if wait fails

    page_num = 0
    while True:
        # Use page_source directly instead of XPath query - much faster
        source_code = driver.page_source

        # Use context manager for file handling
        filename = u'{}{},{},{}.html'.format(TICKET_DIR, from_city, to_city, page_num + 1)
        with codecs.open(filename, 'w', 'utf8') as f:
            f.write(source_code)

        print "page: %d" % (page_num + 1)

        try:
            next_page = driver.find_element_by_id('nextXI3')
            next_page.click()
            # Use shorter wait with explicit condition
            time.sleep(2)
            page_num += 1
        except Exception as e:
            break

def get_proxy_list(file_path):
    """Read proxy list from file - use context manager and strip for cleaner code"""
    proxy_list = []
    try:
        with open(file_path, 'r') as f:
            proxy_list = [line.strip() for line in f if line.strip()]
    except Exception as e:
        print e
    return proxy_list

def ticket_worker_proxy(city_proxy):
    city, proxy_addr = city_proxy.split(',', 1)  # Split only once for efficiency
    proxy = Proxy({
        'proxyType': ProxyType.MANUAL,
        'httpProxy': proxy_addr,
        'ftpProxy': proxy_addr,
        'sslProxy': proxy_addr,
        'noProxy': ''
    })
    driver = webdriver.Firefox(proxy=proxy)
    try:
        driver.get(site)
        driver.maximize_window()
        for to_city in hot_city_list:
            if city != to_city:
                one_driver_ticket(driver, city, to_city)
    finally:
        driver.quit()  # Use quit() instead of close() to properly clean up

def all_ticket_proxy():
    proxy_list = get_proxy_list('./proxy/proxy.txt')
    # Use list comprehension and zip for cleaner code
    hot_city_proxy_list = [city + ',' + proxy for city, proxy in zip(hot_city_list, proxy_list)]
    # Use more processes for parallelism - one per city
    pool = mp.Pool(processes=min(num, mp.cpu_count()))
    pool.map(ticket_worker_proxy, hot_city_proxy_list)
    pool.close()
    pool.join()

def ticket_worker_no_proxy(city):
    driver = webdriver.Firefox()
    try:
        driver.get(site)
        driver.maximize_window()
        # Use WebDriverWait instead of fixed sleep
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.NAME, 'fromCity')))
        for to_city in hot_city_list:
            if city != to_city:
                one_driver_ticket(driver, city, to_city)
    finally:
        driver.quit()  # Use quit() instead of close() to properly clean up

def all_ticket_no_proxy():
    # Use more processes for parallelism - one per city
    pool = mp.Pool(processes=min(num, mp.cpu_count()))
    pool.map(ticket_worker_no_proxy, hot_city_list)
    pool.close()
    pool.join()


if __name__ == '__main__':
    print "start"
    start = datetime.datetime.now()
    # all_ticket_proxy() # proxy
    all_ticket_no_proxy() # no proxy
    end = datetime.datetime.now()
    print "end"
    print "time: ", end-start
