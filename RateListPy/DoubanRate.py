# -*- coding: UTF-8 -*-

'''
Created on Nov 6, 2012

@author: Robert
'''

import StringIO
import urllib2
import gzip
from BeautifulSoup import BeautifulSoup
import codecs
import MySQLdb
import sys
import random
import cookielib
import time

class DoubanRate:

    def __init__(self, base_url):
        self.__base_url = base_url
        self.__rate_file= codecs.open('douban_rate.csv', 'w', 'utf-8')
        self.__rate_file.write(codecs.BOM_UTF8) # make sure Chinese display well in excel
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
        header['Referer']='http://movie.douban.com/'
        user_agents = [
                    'Mozilla/5.0 (Windows; U; Windows NT 5.1; it; rv:1.8.1.11) Gecko/20071127 Firefox/2.0.0.11',
                    'Opera/9.25 (Windows NT 5.1; U; en)',
                    #'Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; SV1; .NET CLR 1.1.4322; .NET CLR 2.0.50727)',
                    #'Mozilla/5.0 (compatible; Konqueror/3.5; Linux) KHTML/3.5.5 (like Gecko) (Kubuntu)',
                    #'Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.8.0.12) Gecko/20070731 Ubuntu/dapper-security Firefox/1.5.0.12',
                    #'Lynx/2.8.5rel.1 libwww-FM/2.14 SSL-MM/1.4.1 GNUTLS/1.2.9',
                    #'Mozilla/5.0 (X11; Linux i686) AppleWebKit/535.7 (KHTML, like Gecko) Ubuntu/11.04 Chromium/16.0.912.77 Chrome/16.0.912.77 Safari/535.7',
                    #'Mozilla/5.0 (X11; Ubuntu; Linux i686; rv:10.0) Gecko/20100101 Firefox/10.0',
                    'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.11 (KHTML, like Gecko) Chrome/23.0.1271.97 Safari/537.11'
                    ]
        header['User-Agent'] = random.choice(user_agents)
        print header['User-Agent']
        #header['Cookie'] = '__gads=ID=d81723387095c254:T=1300016403:S=ALNI_Mao3WCiE08Fb865F6OGkdmPxHiReA; ll="108296"; ct=y; regfromurl=http://movie.douban.com/subject/1474045/; regfromtitle=%E7%9B%97%E8%B5%B0%E8%BE%BE%E8%8A%AC%E5%A5%87%20(%E8%B1%86%E7%93%A3); bid="hg42GBrjo9Q"; viewed="10574622_1474045_1300299_2030778_1424334_1296141_1316580_19955821_5919538_1915403"; __utma=223695111.1246781453.1301999186.1357361023.1357364951.23; __utmb=223695111.10.8.1357364987003; __utmc=223695111; __utmz=223695111.1357306794.17.1.utmcsr=(direct)|utmccn=(direct)|utmcmd=(none); __utma=30149280.1798250085.1322057386.1357361974.1357364951.144; __utmb=30149280.8.10.1357364951; __utmc=30149280; __utmz=30149280.1357361974.143.85.utmcsr=baidu|utmccn=(organic)|utmcmd=organic|utmctr=403%20forbidden%20%E8%B1%86%E7%93%A3%20%E7%88%AC%E8%99%AB; __utmv=30149280.191; RT=s=1357365195009&r=http%3A%2F%2Fmovie.douban.com%2Ftag%2F%25E7%25A7%2591%25E5%25B9%25BB%3Fstart%3D120%26type%3DT'
        
        return header

    def __del__(self):
        self.__rate_file.close()
        self.__cursor.close()
        self.__conn.commit()
        self.__conn.close()


    def parse_item_info(self, tag):
        return True
    def generate_file_content(self, record, movie_name, movie_url, movie_desc, movie_rate, movie_comment_num):
        record = record + ','.join([self.__dimension, self.__tag_name, movie_name, movie_url, movie_desc, movie_rate, movie_comment_num]) + '\n'
        return record
    
    def save_to_file(self, record):
        self.__rate_file.write(record);
        
    def insert_to_db(self, movie_name, movie_url, movie_desc, movie_rate, movie_comment_num):
        try:
            self.__cursor.execute("insert into douban_rate (dimension, tag_name, movie_name, movie_url, movie_desc, movie_rate, movie_comment_num) values (%s, %s, %s, %s, %s, %s, %s)", (self.__dimension, self.__tag_name, movie_name, movie_url, movie_desc, movie_rate, movie_comment_num))
        except MySQLdb.Error, e:
            print 'Error %d: %s' % (e.args[0], e.args[1])
    
    def commit_to_db(self):
        self.__conn.commit()
        
    def open_page(self, url):
        '''
        req = urllib2.Request(url, headers = self.__header)
        return urllib2.urlopen(req, timeout=20)
        '''
        cookie_support= urllib2.HTTPCookieProcessor(cookielib.CookieJar())
        opener = urllib2.build_opener(cookie_support,urllib2.HTTPHandler)
        urllib2.install_opener(opener)
        req = urllib2.Request(url, headers = self.__header)
        return opener.open(req, timeout=20)
        
    def parse_page(self, url):
        time.sleep(1)
        print url
        self.set_page_url(url)
        res = self.open_page(url)
        #req.add_header('Referer','http://movie.douban.com/')
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
                    #encoding because movie_comment_num is type of Unicode, can't be handled by str.isdigit
                    #encoding is to Unicode2String
                    movie_comment_num = filter(str.isdigit, movie_comment_num.encode('utf-8'))
                else:
                    movie_rate = None
                    movie_comment_num = None
                
                if movie_name is not None:
                    movie_url = movie_url if movie_url is not None else ''
                    movie_desc = movie_desc if movie_desc is not None else ''
                    movie_rate = movie_rate if movie_rate is not None else '0.0'
                    movie_comment_num = movie_comment_num if (movie_comment_num is not None)&(movie_comment_num != '') else '0'  #must use: != '' but not using: is not ''
                    record = self.generate_file_content(record, movie_name, movie_url, movie_desc, movie_rate, movie_comment_num)
                    self.insert_to_db(movie_name, movie_url, movie_desc, movie_rate, movie_comment_num)
            
            self.save_to_file(record)
            self.commit_to_db()

            url = self.get_next_page_url(soup)
            if url is not None:
                self.parse_page(url)
        res.close()
            
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
            if next_page.find('a') is not None:
                next_page_url = next_page.a['href']
                return next_page_url
        else:
            return None

    def fetch_info(self):
        res = self.open_page(self.__base_url)
        html = res.read()
        html = gzip.GzipFile(fileobj=StringIO.StringIO(html)).read()
        soup = BeautifulSoup(html)
        for tb in soup.findAll('table', {'class':'tagCol'}):
            dimension = self.get_dimension(tb)
            self.set_dimension(dimension)
            print self.__dimension
            for tag_name_tag in self.get_tag_name_tags(tb):
                self.set_tag_name(tag_name_tag)
                print self.__tag_name
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
    #rate.parse_page('http://movie.douban.com/tag/%E7%A7%91%E5%B9%BB?start=100&type=T')
    print 'task ends!'

        