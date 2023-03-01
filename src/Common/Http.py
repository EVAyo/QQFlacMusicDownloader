#  Copyright (c) 2023. 秋城落叶, Inc. All Rights Reserved
#  @作者         : 秋城落叶(QiuChenly)
#  @邮件         : 1925374620@qq.com
#  @文件         : 项目 [qqmusic] - Http.py
#  @修改时间    : 2023-03-02 01:38:08
#  @上次修改    : 2023/3/2 上午1:02

import json

import requests

# 全局唯一Session
session = requests.Session()


def getHttp(url: str, method: int = 0, data: bytes = r'', header: dict = {}) -> requests.Response:
    """
    Http请求-提交二进制流
    Args:
        url: url网址
        method: 0 表示Get请求 1 表示用POST请求. 默认值为 0.
        data: 提交的二进制流data数据. 默认值为 r''.
        header: 协议头. 默认值为 {}.

    Returns:
        requests.Response: 返回的http数据
    """
    if method == 0:
        d = session.get(url, headers=header)
    else:
        d = session.post(url, data, headers=header)
    return d


def getHttp2Json(url: str, method: int = 0, data: dict = {}, header: dict = {}):
    """Http请求-提交json数据

    Args:
        url (str): url网址
        method (int): 0 表示Get请求 1 表示用POST请求. 默认值为 0.
        data (bytes): 提交的json对象数据. 默认值为 {}.
        header (dict): 协议头. 默认值为 {}.

    Returns:
        requests.Response: 返回的http数据
    """
    d = json.dumps(data, ensure_ascii=False)
    d = d.encode('utf-8')
    return getHttp(url, method, d, header)
