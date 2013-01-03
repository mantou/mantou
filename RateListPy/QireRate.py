# -*- coding: UTF-8 -*-

'''
Created on Oct 20, 2012

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
import re


class QireRate:
    
    def __init__(self, base_url, file_name):
        self.__base_url = base_url
        self.__header = self.set_header()
        try:
            self.__rate_file = codecs.open(file_name, 'w', 'utf-8')
            self.__rate_file.write(codecs.BOM_UTF8)
        except:
            print "Not able to create a file to store result! No permission to create that file?"
        try:
            self.__conn=MySQLdb.connect(host='localhost',user='test',passwd='test', db='test', port=3306, charset='utf8')
            self.__cursor = self.__conn.cursor()
            self.__cursor.execute("truncate table qire_rate")
            self.__conn.commit()
        except MySQLdb.Error, e:
            print 'Error %d: %s' % (e.args[0], e.args[1])
            print 'Not able to get a mysql connection successfully. Is mysql running?!'
            sys.exit(1)
        
    def __del__(self):
        self.__rate_file.close()
        self.__cursor.close()
        self.__conn.commit()
        self.__conn.close()

    # this all to make sure we can get the right response from server
    # set host, referer incase there is some anti robot crawling rules running on server
    def set_header(self):
        header = dict()
        header['Accept']='application/json, text/javascript, */*; q=0.01'
        header['Accept-Charset']='GBK,utf-8;q=0.7,*;q=0.3'
        header['Accept-Encoding']='gzip,deflate,sdch'
        header['Accept-Language']='en-US,en;q=0.8,zh-CN;q=0.6,zh;q=0.4'
        header['Host']='www.qire123.com'
        header['Proxy-Connection']='keep-alive'
        header['Referer']='http://www.qire123.com/vod-showlist-id-8-order-hits.html'
        # remove below line because somehow can't make the conntion with it
        #header['User-Agent']='Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.4 (KHTML, like Gecko) Chrome/22.0.1229.94 Safari/537.4'
        header['X-Requested-With']='XMLHttpRequest'  #this ensure we make the request through ajax and can get the json data back from it
        
        return header

    def get_XHR_response(self, url):
        req = urllib2.Request(url)
        # initial request header by header dict
        for key, val in self.__header.items():
            req.add_header(key, val)
        try:
            res = urllib2.urlopen(req, timeout=5)
        except:
            return None
            
        headerObject = res.headers
        streamData = ""
        while True:
            subData = res.read(2048)
            if subData == "":
                break
            streamData = streamData + subData
    
        if headerObject.has_key('Content-Encoding'):
            if cmp(headerObject['Content-Encoding'].strip().upper(), 'gzip'.upper()) == 0:  
                compresseddata = streamData
                compressedstream = StringIO.StringIO(compresseddata)
                gzipper = gzip.GzipFile(fileobj=compressedstream)
                htmlCode = gzipper.read()
            else:
                htmlCode = streamData
        else:
            htmlCode = streamData

        if headerObject.has_key('Content-Type'):
            contentType = headerObject['Content-Type']
            if contentType.lower().find('charset=') != -1:
                charset = re.search(r'charset=([^;]*)', contentType.lower()).group(1)  
                if charset != 'utf-8':
                    try:
                        htmlCode = htmlCode.decode(charset).encode('utf-8')
                    except:
                        pass
        res.close()
        return htmlCode

    def get_link_tag(self, tag):
        return tag.contents[0]
    def get_rate(self, tag):
        return tag.findNextSiblings('p', {'class':'count'})[0].find('strong', {'class':'ratbar-num'}).string
    def get_name(self, tag):
        return tag.string
    def get_link_url(self, tag):
        return tag['href']
    def get_video_format(self, tag):
        return tag.findNextSiblings('p', {'class':'state'})[0].find('a', {'class':'goplay'}).string
    def get_current_page_id(self, soup):
        return soup.find('span', {'class':'current'}).string
    def get_nextpage_url(self, soup):
        # the htmlCode has the Chinese encoded like \u3a0d
        # by doing below json loads, it turns back to Chinese
        #pages = json.loads(htmlCode)['pages'] #get value of key 'pages'
        #soup = BeautifulSoup(pages)
        # find all tags with tag name 'a' and class = 'next pagegbk', next page
        nextpage_tag = soup.find('a', {'class':'next pagegbk'})
        if nextpage_tag != None:
            nextpage_link = self.__base_url + nextpage_tag['href'] # get link full address
        else:
            nextpage_link = None
        return nextpage_link
        
    def parse_html(self, url):
        req = urllib2.Request(url)
        res = urllib2.urlopen(req, timeout=5)
        html= res.read()
        res.close()
        print "working on page:  1"
        soup = BeautifulSoup(html)
        category = soup.find(id = "byletter")['href'].strip('/')
        for tag in soup.findAll('h5'):
            rate = self.get_rate(tag)
            link_tag = self.get_link_tag(tag)
            name = self.get_name(link_tag)
            link = self.get_link_url(link_tag)
            video_format = self.get_video_format(tag)
            self.save_to_file(category, '1', rate, name, link, video_format)
            self.save_to_db(category, '1', rate, name, link, video_format)

        nextpage_url = self.get_nextpage_url(soup)
        if nextpage_url != None:
            self.fetch_info(nextpage_url)
            
    def parse_json(self, url):
        json_res = self.get_XHR_response(url)
        if json_res != None:
            # get category name, from key 'letterurl'. orignal value is /action/
            category = '%s' %json.loads(json_res)['letterurl'].strip('/')
            pages = json.loads(json_res)['pages']
            soup = BeautifulSoup(pages)
            current_page_id = self.get_current_page_id(soup)
            print "working on page: ", current_page_id
            nextpage_url = self.get_nextpage_url(soup)
            # the major part of json data contains all the video information
            ajaxtxt = json.loads(json_res)['ajaxtxt']
            soup = BeautifulSoup(ajaxtxt)
            for tag in soup.findAll('h5'):
                rate = self.get_rate(tag)
                link_tag = self.get_link_tag(tag)
                name = self.get_name(link_tag)
                link = self.get_link_url(link_tag)
                video_format = self.get_video_format(tag)
                self.save_to_file(category, current_page_id, rate, name, link, video_format)
                self.save_to_db(category, current_page_id, rate, name, link, video_format)
            
            # recursively get the data if it is not last page
            if nextpage_url != None:# if nextpage == None, means this is the last page, so return
                # self call to do recursively fetch
                self.parse_json(nextpage_url)
        else:
            print 'skiping page: ' + url
            list_tmp = url.split('-')  # split url by '-'
            #prefix like http://www.qire123.com/vod-showlist-id-8-order-hits-c-2703-p
            prefix = '-'.join(list_tmp[:-1])
            
            list_tmp = list_tmp[-1].split('.')  # split "100.html" by '.'
            current_page_id = list_tmp[0]   # get "100"
            
            #current_page_id = '%d' %current_page_id
            current_page_id = int(current_page_id)  #convert "100" to int 100
            next_page_id = current_page_id + 1  # get next page id: 101
            next_page_id = str(next_page_id) #convert page id to string
            
            suffix = '.'.join([next_page_id, list_tmp[-1]])  # suffix like '101.html'
            url = '-'.join([prefix, suffix])  # get next page url
            print 'go to next page, page id: ' + next_page_id
            self.parse_json(url)
            
    def fetch_info(self, url):
        if url.find("order-hits.html") > 0:
            self.parse_html(url)
        else:
            self.parse_json(url)

    
    def save_to_file(self, category, page_id, rate, name, link, video_format):
        record = category + ',' + page_id + ',' + rate + ',' + name + ',' + link + ',' + video_format
        try:
            self.__rate_file.write(record + '\n')
        except:
            print 'Having trouble to save this record to file: ', record
        
    def save_to_db(self, category, page_id, rate, name, link, video_format):
        try:
            self.__cursor.execute("insert into qire_rate (category, page_id, rate, name, link, format) values (%s, %s, %s, %s, %s, %s)", (category, page_id, rate, name, link, video_format))
        except MySQLdb.Error, e:
            print 'Error %d: %s' % (e.args[0], e.args[1])
            print "this is the record making trouble:  ", category + ',' + page_id + ',' + rate + ',' + name + ',' + link + ',' + video_format

if __name__ == '__main__':
    
    base_url = "http://www.qire123.com"
    file_name = "rate_file.csv"
    rate = QireRate(base_url, file_name)
    print 'task starts!'
    for category_id in (8,9,10,11,12,13,14,23,31,17):
        print 'working on category: ', category_id
        start_url = base_url + "/vod-showlist-id-" + str(category_id) + "-order-hits.html"
        #start_url = base_url + "/vod-showlist-id-" + str(category_id) + "-order-hits-c-2703-p-90.html"
        rate.fetch_info(start_url)
    print 'task ends!'
    