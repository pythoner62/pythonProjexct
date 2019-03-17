#!/usr/bin/python
# -*- coding: utf-8 -*-
__author__ = 'Sunny'
import pymongo
import time
import urllib3
urllib3.disable_warnings()
import re
from commonRequests import make_session
from lxml import etree
'''
描述；爬取易车网的社区栏目下的车型社区的各种车型专区的前十遍精华帖的内容，
      包括帖子的作者，标题，内容，发布时间等字段信息。
思路；从开始首个 URL进行访问，会得到下一级的URL，再从下一级的URL中得到再下一级的URL，一直到想要的页面。
      这个过程用到的for循环较多，所以选择了用yield 将返回的响应和数据都是通过生成器来传递，而不用list，大大提高了效率。
难点；页面层级关系比较紧密，请求次数较多，开启for循环遍历对印好请求信息避免出错，
      提取内容字段的时候，要注意多层标签中嵌套内容，需要先匹配出这块模板标签的内容，
      再用xpath函数string()匹配标签下的所有内容。
'''
class Mongodb_class:
    '''
        数据库连接的类
    '''
    def __init__(self,host='127.0.0.1',port=27017):
        '''
        :param host: 要连接的ip
        :param port: 端口号
        '''
        self.client = pymongo.MongoClient(host,port)

    def choice_db_collection(self,db_first,collection):
        self.db = self.client[db_first]
        self.coll = self.db[collection]

    def insert_data(self,data):
        self.coll.insert(data)

    def db_close(self):
        self.client.close()


class Taoche:

    def __init__(self, url):
        '''
        :param session: 重写的session的类，扩充了headers，代理IP
        :param url:  开始访问的url
        '''
        self.session = make_session()
        self.url = url

    def visit_index(self,url):
        response = self.session.get(url)
        if response.status_code == 200:
            # print("访问visit_index成功 ！")
            tree = etree.HTML(response.text)
            self.url_list = tree.xpath('//ul[@class="list-con"]/li/ul/li/a/@href')
            # print(self.url_list)

    def visit_list_url(self):
        for url in self.url_list:
            headers = {"Referer":self.url}
            response = self.session.get(url,headers=headers)
            if response.status_code == 200:
                # print('访问list_url成功！！！')
                urls_num = re.findall('<li><a target="_blank" href="(.*?)" ><span>.*?</span></a></li>', response.text, re.S)
                if urls_num != []:
                    # findall匹配会匹配到空的【】所以要将没用的清除
                    yield urls_num

    def visit_set_url_request(self):
         for urls in self.visit_list_url():
            for url in urls:
                # print(url)
                referer = 'https://baa.bitauto.com' + url + '/'
                # 拼接的URL 也就是上一步的referer
                url = referer + "index-0-all-1-0.html"
                # 拼接首页的URL，要求只要前十遍的内容，所以只要第一页的内容。
                headers = {"Referer": referer}
                response = self.session.get(url, headers=headers)
                if response.status_code == 200:
                    # print('访问set_url_request成功！！！')
                    yield response,url

    def visit_postlist_url(self):
        for response,referer in self.visit_set_url_request():
            tree = etree.HTML(response.text)
            user_name = tree.xpath('//*[@id="divTopicList"]/div[3]/ul/li[5]/a/text()')
            post_times = tree.xpath('//*[@id="divTopicList"]/div[3]/ul/li[5]/span/text()')
            postslist_url = tree.xpath('//div[@class="postslist_xh"]/ul/li[@class="tu"]/a/@href')
            if len(postslist_url) > 10 :
                postslist_url = postslist_url[:10]
                user_name = user_name[:10]
                for url,user,times in zip(postslist_url, user_name, post_times):
                    headers = {'Referer': referer}
                    resp = self.session.get(url, headers=headers)
                    if resp.status_code == 200 :
                        # print("访问postslist_url成功 ！！！")
                        yield resp,user,times

    def get_data(self):
        def clear_data(data):
            '''
            :param data: 传入要清洗的数据
            :return: 清洗操作后返回的数据
            '''
            return data.replace(' ','').replace('\r','').replace('\n','')

        for response,user,times in self.visit_postlist_url():
            tree = etree.HTML(response.text)
            title = tree.xpath('//head/title/text()')[0]
            user = clear_data(user)
            times = clear_data(times)
            div = tree.xpath('//div[@class="post_width"]')[0]
            koubeilist = clear_data(div.xpath('string(.)'))
            yield {
                'title': title,
                'user_name': user,
                'pub_time': times,
                'koubeilist': koubeilist
                }

    def start_run(self):
        t = time.time()
        self.visit_index(self.url)
        self.visit_set_url_request()
        self.visit_postlist_url()
        m = Mongodb_class()
        db = 'db_first'
        coll = 'taoche_spider'
        m.choice_db_collection(db, coll)
        for data in self.get_data():
            # print(data)
            try :
                m.insert_data(data)
            finally:
                m.db_close()
        e = time.time()
        print('爬取结束,总耗时:', e-t)

if __name__ == "__main__":
    url = "https://baa.bitauto.com/foruminterrelated/brandforumlist.html"
    taoche = Taoche(url)
    taoche.start_run()