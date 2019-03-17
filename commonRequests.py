#!/usr/bin/python
# -*- coding: utf-8 -*-
__author__ = 'Sunny'

import requests

def make_session(is_proxy=False):
    session = requests.session() #构造一个通用的requests的session对象
    session.verify = False # 不检验 https 证书
    session.trust_env = False  #设置不信任系统代理，并且不启用

    #设置默认的headers,基本通用
    session.headers = {
        'Connection': 'keep-alive',
        'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
        'Accept-Language': 'zh-CN,zh;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br'
    }
    if is_proxy :
        session.proxies = {
            'http': '127.0.0.1:8888',
            'https': '127.0.0.1:8888',
        }
    return session  # 返回session对象
