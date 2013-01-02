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
        self.__qire_header = self.__set_qire_header()
        self.__douban_header = self.__set_douban_header()
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
    def __set_qire_header(self):
        httpheader = dict()
        httpheader['Accept']='application/json, text/javascript, */*; q=0.01'
        httpheader['Accept-Charset']='GBK,utf-8;q=0.7,*;q=0.3'
        httpheader['Accept-Encoding']='gzip,deflate,sdch'
        httpheader['Accept-Language']='en-US,en;q=0.8,zh-CN;q=0.6,zh;q=0.4'
        httpheader['Host']='www.qire123.net'
        httpheader['Proxy-Connection']='keep-alive'
        httpheader['Referer']='http//www.qire123.net/vod-showlist-id-8-order-hits.html'
        # remove below line because somehow can't make the conntion with it
        #httpheader['User-Agent']='Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.4 (KHTML, like Gecko) Chrome/22.0.1229.94 Safari/537.4'
        httpheader['X-Requested-With']='XMLHttpRequest'  #this ensure we make the request through ajax and can get the json data back from it
        
        return httpheader
    
    def __set_douban_header(self):
        httpheader = dict()
        httpheader['Accept']='application/json, text/javascript, */*; q=0.01'
        httpheader['Accept-Charset']='GBK,utf-8;q=0.7,*;q=0.3'
        httpheader['Accept-Encoding']='gzip,deflate,sdch'
        httpheader['Accept-Language']='en-US,en;q=0.8,zh-CN;q=0.6,zh;q=0.4'
        httpheader['Host']='movie.douban.com'
        httpheader['Proxy-Connection']='keep-alive'
        httpheader['Referer']='http://movie.douban.com/'
        # remove below line because somehow can't make the conntion with it
        #httpheader['User-Agent']='Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.4 (KHTML, like Gecko) Chrome/22.0.1229.94 Safari/537.4'
        httpheader['X-Requested-With']='XMLHttpRequest'
        
        return httpheader
        
    def get_nextpage(self, htmlCode):
        # the htmlCode has the Chinese encoded like \u3a0d
        # by doing below json loads, it turns back to Chinese
        pages = json.loads(htmlCode)['pages'] #get value of key 'pages'
        soup = BeautifulSoup(pages)
        # find all tags with tag name 'a' and class = 'next pagegbk', next page
        nextpage_tag = soup.find('a', {'class':'next pagegbk'})
        if nextpage_tag != None:
            nextpage_link = nextpage_tag['href'] # get link address
        else:
            nextpage_link = None
        return nextpage_link
        
    def get_XHR_response(self, url, header):
        req = urllib2.Request(url)
        # initial request header by header dict
        for key, val in header.items():
            req.add_header(key, val)
        res = urllib2.urlopen(req)
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
        print htmlCode
        return htmlCode
    
    def fetch_rate(self, url):
        qire_html_res = self.get_XHR_response(url, self.__qire_header)
        # get category name, from key 'letterurl'. orignal value is /action/
        category = '%s' %json.loads(qire_html_res)['letterurl']
        category = category.strip('/')
        pages = json.loads(qire_html_res)['pages']
        soup = BeautifulSoup(pages)
        current_page_id = soup.find('span', {'class':'current'}).string
        print "working on page: ", current_page_id
        # the major part of json data contains all the video information
        ajaxtxt = json.loads(qire_html_res)['ajaxtxt']
        soup = BeautifulSoup(ajaxtxt)
        for tag in soup.findAll('h5'):
            link_tag = tag.contents[0]
            score_tag = tag.findNextSiblings('p', {'class':'count'})[0].find('strong', {'class':'ratbar-num'})
            video_tag = tag.findNextSiblings('p', {'class':'state'})[0].find('a', {'class':'goplay'})
            record = category + ',' + current_page_id + ',' + score_tag.string + ',' + link_tag.string + ',' + link_tag['href'] + ',' + video_tag.string
            douban_url = 'http://movie.douban.com/j/subject_suggest?q='+urllib2.quote(link_tag.string.encode('utf-8'))
            douban_html_res = json.loads(self.get_XHR_response(douban_url, self.__douban_header))
            if (len(douban_html_res) > 0):
                douban_url = '%s' %douban_html_res[0]['url'].replace('\\', '')
                douban_page = urllib2.urlopen(douban_url)
                douban_soup = BeautifulSoup(douban_page,fromEncoding="utf-8")
                douban_tag = douban_soup.find('strong', {'class':'ll rating_num'})
                if douban_tag != None:
                    record = record + ',' + '%s' %douban_tag.string
            else:
                print 'can not find ' + link_tag.string + ' on Douban'
            self.__rate_file.write(record + '\n')
            try:
                self.__cursor.execute("insert into qire_rate (category, page_id, rate, name, link, format) values (%s, %s, %s, %s, %s, %s)", (category, current_page_id, score_tag.string, link_tag.string, link_tag['href'], video_tag.string))
            except MySQLdb.Error, e:
                print 'Error %d: %s' % (e.args[0], e.args[1])
                print "this is the record making trouble:  ", record
                
        # recursively get the data if it is not last page
        nextpage = self.get_nextpage(qire_html_res)
        self.get_nextpage(qire_html_res)
        if nextpage != None:
            nextpage = self.__base_url + nextpage
            # self call to do recursively fetch
            self.fetch_rate(nextpage)
        # if nextpage == None, means this is the last page, so return

if __name__ == '__main__':
    
    base_url = "http://www.qire123.com"
    file_name = "rate_file.csv"
    rate = QireRate(base_url, file_name)
    print 'task starts!'
    for category_id in range(8, 9):
        print 'working on category: ', category_id
        start_url = base_url + "/vod-showlist-id-" + str(category_id) + "-order-hits.html"
        rate.fetch_rate(start_url)
    print 'task ends!'
        
    