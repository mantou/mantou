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
        #self.__douban_header = self.__set_douban_header()
        self.header = dict()
        self.header['Accept']='application/json, text/javascript, */*; q=0.01'
        self.header['Accept-Charset']='GBK,utf-8;q=0.7,*;q=0.3'
        self.header['Accept-Encoding']='gzip,deflate,sdch'
        self.header['Accept-Language']='en-US,en;q=0.8,zh-CN;q=0.6,zh;q=0.4'
        self.header['Host']='movie.douban.com'
        self.header['Proxy-Connection']='keep-alive'
        self.header['User-Agent']='Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.4 (KHTML, like Gecko) Chrome/22.0.1229.94 Safari/537.4'

        try:
            self.__conn=MySQLdb.connect(host='localhost',user='test',passwd='test', db='test', port=3306, charset='utf8')
            self.__cursor = self.__conn.cursor()
            self.__cursor.execute("truncate table douban_rate")
            self.__conn.commit()
        except MySQLdb.Error, e:
            print 'Error %d: %s' % (e.args[0], e.args[1])
            print 'Not able to get a mysql connection successfully. Is mysql running?!'
            sys.exit(1)
    
    def __del__(self):
        self.__cursor.close()
        self.__conn.commit()
        self.__conn.close()
        
    def fetch_movie(self, link, dimension, tag_name):
        print link
        req = urllib2.Request(link)
        req.add_header('Referer','http://movie.douban.com/')
        res = urllib2.urlopen(req)
        html = res.read()
        soup = BeautifulSoup(html)
        movie_name = ''
        movie_desc = ''
        movie_rate = ''
        movie_comment_num = ''
        tr = soup.find('tr', {'class':'item'})
        if tr != None:
            for tr in soup.findAll('tr', {'class':'item'}):
                record = dimension + ',' + tag_name
                
                movie_name = tr.find('div', {'class':'pl2'}).find('a').text
                movie_desc = tr.find('p', {'class':'pl'}).string
                rate = tr.find('div', {'class':'star clearfix'})
                movie_rate = rate.find('span', {'class':'rating_nums'}).string
                movie_comment_num = rate.find('span', {'class':'pl'}).string
                
                if (movie_rate == None) and (movie_comment_num == None):
                    record = record + ',' + movie_name + ',' + movie_desc
                elif movie_rate != None:
                    record = record + ',' + movie_name + ',' + movie_desc + ',' + movie_rate
                elif movie_comment_num != None:
                    record = record + ',' + movie_name + ',' + movie_desc + ',' + movie_rate + ',' + movie_comment_num
                print "movie_name:"
                print movie_name
                print "rate:"
                print movie_rate
                print "comment:"
                print movie_comment_num
                self.__rate_file.write(record + '\n')
            nextpage = soup.find('span', {'class':'next'}).a['href']
            
            
            '''
            try:
                self.__cursor.execute("insert into qire_rate (category, page_id, rate, name, link, format) values (%s, %s, %s, %s, %s, %s)", (category, current_page_id, score_tag.string, link_tag.string, link_tag['href'], video_tag.string))
            except MySQLdb.Error, e:
                print 'Error %d: %s' % (e.args[0], e.args[1])
                print "this is the record making trouble:  ", record
            '''
            self.fetch_movie(nextpage, dimension, tag_name)
            
            

    def fetch_rate(self):
        req = urllib2.Request(self.__base_url)
        for key, val in self.header.items():
            req.add_header(key, val)
        res = urllib2.urlopen(req)
        html = res.read()
        html = gzip.GzipFile(fileobj=StringIO.StringIO(html)).read()
        soup = BeautifulSoup(html)
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

if __name__ == '__main__':
    
    base_url = "http://movie.douban.com/tag/"
    rate = DoubanRate(base_url)
    print 'task starts!'
    rate.fetch_rate()
    print 'task ends!'
        