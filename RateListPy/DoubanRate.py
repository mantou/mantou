# -*- coding: UTF-8 -*-

'''
Created on Nov 6, 2012

@author: Robert
'''

import pycurl
import StringIO
import urllib2
import urllib
import gzip
import json
from BeautifulSoup import BeautifulSoup
import codecs
import MySQLdb
import sys


class DoubanRate:
    
    def __init__(self, base_url):
        self.__base_url = base_url
        self.__rate_file= codecs.open('douban_rate.csv', 'w', 'utf-8')
        self.__rate_file.write(codecs.BOM_UTF8) # make sure Chinese display well in excel
        #self.__douban_header = self.__set_douban_header()
        self.__dimension = ''
        self.__tag_name = ''
        self.__page_url = ''
        self.__header = self.set_header()
        
        try:
            self.__conn=MySQLdb.connect(host='localhost',user='test',passwd='test', db='test', port=3306, charset='utf8')
            self.__cursor = self.__conn.cursor()
            self.__cursor.execute("truncate table douban_rate")
            self.__conn.commit()
        except MySQLdb.Error, e:
            print 'Error %d: %s' % (e.args[0], e.args[1])
            print 'Not able to get a mysql connection successfully. Is mysql running?!'
            sys.exit(1)
    
    def set_header(self):
        header = dict()
        header['Accept']='text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
        header['Accept-Charset']='GBK,utf-8;q=0.7,*;q=0.3'
        header['Accept-Encoding']='gzip,deflate,sdch'
        header['Accept-Language']='en-US,en;q=0.8,zh-CN;q=0.6,zh;q=0.4'
        header['Connection']='keep-alive'
        header['Host']='movie.douban.com'
        header['User-Agent']='Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.11 (KHTML, like Gecko) Chrome/23.0.1271.97 Safari/537.11'
        
        return header

    def __del__(self):
        self.__cursor.close()
        #self.__conn.commit()
        self.__conn.close()


    def parse_item_info(self, tag):
        return True
    def generate_file_content(self, record, movie_name, movie_url, movie_desc, movie_rate, movie_comment_num):
        if movie_name is None:
            return record
        if movie_url is None:
            movie_url = ''
        if movie_desc is None:
            movie_desc = ''
        if movie_rate is None:
            movie_rate = ''
        if movie_comment_num is None:
            movie_comment_num = ''

        record = ','.join([self.__dimension, self.__tag_name, movie_name, movie_url, movie_desc, movie_rate, movie_comment_num]) + '\n'
        return record
    
    def save_to_file(self, record):
        self.__rate_file.write(record);
        
    def insert_to_db(self, movie_name, movie_url, movie_desc, movie_rate, movie_comment_num):
        try:
            self.__cursor.execute("insert into douban_rate (dimension, tag_name, movie_name, movie_url, movie_desc, movie_rate, movie_comment_num) values (%s, %s, %s, %s, %s, %s, %s)", (self.__dimension, self.__tag_name, movie_name, movie_url, movie_desc, movie_rate, movie_comment_num))
        except MySQLdb.Error, e:
            print 'Error %d: %s' % (e.args[0], e.args[1])
    
    def commit_to_db(self):
        self.__conn.commit
        
    def parse_page(self, url):
        print url
        self.set_page_url(url)
        req = urllib2.Request(url)
        for key, val in self.__header.items():
            req.add_header(key, val)
        req.add_header('Referer','http://movie.douban.com/')
        res = urllib2.urlopen(req, timeout=20)
        html = res.read()
        html = gzip.GzipFile(fileobj=StringIO.StringIO(html)).read()
        soup = BeautifulSoup(html)
        item_tags = soup.findAll('tr', {'class':'item'})
        if item_tags is not None:
            record = ''
            for item_tag in item_tags:
                movie_name = item_tag.find('div', {'class':'pl2'}).find('a').text
                movie_url = item_tag.find('div', {'class':'pl2'}).find('a')['href']
                movie_desc = item_tag.find('p', {'class':'pl'}).string
                rate_tag = item_tag.find('div', {'class':'star clearfix'})
                if rate_tag is not None:
                    movie_rate = rate_tag.find('span', {'class':'rating_nums'}).string
                    movie_comment_num = rate_tag.find('span', {'class':'pl'}).string
                else:
                    movie_rate = ''
                    movie_comment_num = ''
                
                record = self.generate_file_content(record, movie_name, movie_url, movie_desc, movie_rate, movie_comment_num)
                self.insert_to_db(movie_name, movie_url, movie_desc, movie_rate, movie_comment_num)
            self.save_to_file(record)
            self.commit_to_db()

            url = self.get_next_page_url(soup)
            if url is not None:
                self.parse_page(url)
            
    def get_dimension(self, tag):
        return tag.findPreviousSibling('a')['name']
    def set_dimension(self, dimension):
        self.__dimension = dimension
    def get_tag_name_tags(self, tag):
        return tag.findAll('a')
    def set_tag_name(self, tag_name_tag):
        self.__tag_name = tag_name_tag.string
    def get_first_page_url(self, tag):
        return self.__base_url + tag['href']
    def set_page_url(self, url):
        self.__page_url = url

    def get_next_page_url(self, soup):
        next_page = soup.find('span', {'class':'next'})
        if next_page is not None:
            next_page_url = next_page.a['href']
            return next_page_url
        else:
            return None

    def fetch_info(self):
        req = urllib2.Request(self.__base_url)
        for key, val in self.__header.items():
            req.add_header(key, val)
        res = urllib2.urlopen(req, timeout=20)
        html = res.read()
        html = gzip.GzipFile(fileobj=StringIO.StringIO(html)).read()
        soup = BeautifulSoup(html)
        for tb in soup.findAll('table', {'class':'tagCol'}):
            dimension = self.get_dimension(tb)
            self.set_dimension(dimension)
            for tag_name_tag in self.get_tag_name_tags(tb):
                self.set_tag_name(tag_name_tag)
                url = self.get_first_page_url(tag_name_tag)
                self.parse_page(url)
                
                
        
        '''        
        category = soup.find('a', {'name':'类型'})
        dimension_num = 1
        dimension = ''
        #table = category.findNextSiblings('table', {'class':'tagCol'})[0]
        for tb in soup.findAll('table', {'class':'tagCol'}):
            if dimension_num == 3:
                continue
            dimension = {
             1: lambda dimension: 'category',
             2: lambda dimension: 'country',
             3: lambda dimension: 'actor',
             4: lambda dimension: 'year'
            }[dimension_num](dimension)
            for tr in tb.findAll('tr'):
                for td in tr.findAll('td'):
                    tag = td.find('a')
                    tag_name = tag.string
                    tag_link = tag['href']
                    #html = gzip.GzipFile(fileobj=StringIO.StringIO(html)).read()
                    self.fetch_movie(self.__base_url+tag_link, dimension, tag_name)
            dimension_num = dimension_num + 1
        '''

if __name__ == '__main__':
    
    base_url = "http://movie.douban.com/tag/"
    rate = DoubanRate(base_url)
    print 'task starts!'
    rate.fetch_info()
    print 'task ends!'
        