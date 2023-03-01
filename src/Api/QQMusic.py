#  Copyright (c) 2023. 秋城落叶, Inc. All Rights Reserved
#  @作者         : 秋城落叶(QiuChenly)
#  @邮件         : 1925374620@qq.com
#  @文件         : 项目 [qqmusic] - QQMusic.py
#  @修改时间    : 2023-03-02 03:32:23
#  @上次修改    : 2023/3/2 上午3:32

import json
from src.Common.Http import getHttp2Json

mQQCookie = ""


def getCookie():
    return mQQCookie


def setQQCookie(ck: str):
    global mQQCookie
    mQQCookie = ck


def getHead():
    return {
        "User-Agent": "QQ音乐/73222 CFNetwork/1406.0.2 Darwin/22.4.0".encode("utf-8"),
        "Accept": "*/*",
        "Accept-Language": "zh-CN,zh-Hans;q=0.9",
        "Referer": "http://y.qq.com",
        'Content-Type': 'application/json; charset=UTF-8',
        "Cookie": getCookie(),
    }


def getQQServersCallback(url: str, method: int = 0, data={}):
    """重新设计了Http接口

    参数:
        url (str): _description_
        method (int): _description_. Defaults to 0.
        data (dict): _description_. Defaults to {}.

    返回:
        requests.Response: 返回的http数据
    """
    return getHttp2Json(url, method, data, getHead())


def getQQMusicLyricByWeb(songID: str) -> dict:
    """用QQ音乐网页端的接口获取歌词

    参数:
        songID (str): 歌曲数字序列id

    返回值:
        dict: 返回一个json结构, 通过['lyric']来获取base64后的歌词内容
    """
    url = "https://u.y.qq.com/cgi-bin/musicu.fcg"
    payload = {
        "comm": {
            "cv": 4747474,
            "ct": 24,
            "format": "json",
            "inCharset": "utf-8",
            "outCharset": "utf-8",
            "notice": 0,
            "platform": "yqq.json",
            "needNewCode": 1
        },
        "PlayLyricInfo": {
            "module": "music.musichallSong.PlayLyricInfo",
            "method": "GetPlayLyricInfo",
            "param": {
                # "songMID": "003AUKFs2S1Kwi",
                "songID": songID
            }
        }
    }
    d = getQQServersCallback(url, 1, payload)
    d = d.json()
    d = d['PlayLyricInfo']['data']
    return d


def getQQMusicLyricByMacApp(songID: str) -> dict:
    """从QQ音乐电脑客户端接口获取歌词

    参数:
        songID (str): 音乐id

    返回值:
        dict: 通过['lyric']来获取base64后的歌词内容
    """
    url = "https://u.y.qq.com/cgi-bin/musicu.fcg"
    payload = {
        "music.musichallSong.PlayLyricInfo.GetPlayLyricInfo": {
            "module": "music.musichallSong.PlayLyricInfo",
            "method": "GetPlayLyricInfo",
            "param": {
                "trans_t": 0,
                "roma_t": 0,
                "crypt": 0,  # 1 define to encrypt
                "lrc_t": 0,
                "interval": 208,
                "trans": 1,
                "ct": 6,
                "singerName": "",  # 576K576K
                "type": 0,
                "qrc_t": 0,
                "cv": 80600,
                "roma": 1,
                "songID": songID,  # 391938242
                "qrc": 0,  # 1 define base64 or compress Hex
                "albumName": "",  # 55m96bi9
                "songName": ""  # 55m96bi9
            }
        },
        "comm": {
            "wid": "",
            "tmeAppID": "qqmusic",
            "authst": "",
            "uid": "",
            "gray": "0",
            "OpenUDID": "",
            "ct": "6",
            "patch": "2",
            "psrf_qqopenid": "",
            "sid": "",
            "psrf_access_token_expiresAt": "",
            "cv": "80600",
            "gzip": "0",
            "qq": "",
            "nettype": "2",
            "psrf_qqunionid": "",
            "psrf_qqaccess_token": "",
            "tmeLoginType": "2"
        }
    }
    d = getQQServersCallback(url, 1, payload)
    d = d.json()
    d = d['music.musichallSong.PlayLyricInfo.GetPlayLyricInfo']['data']
    return d


def getQQMusicMediaLyric(mid: str) -> dict:
    """[已经被弃用]早期的歌词下载接口v1

    参数:
        mid (str): 音乐文件的mid

    返回:
        dict: 词典
    """
    d = getQQServersCallback(
        f'https://c.y.qq.com/lyric/fcgi-bin/fcg_query_lyric_new.fcg?songmid={mid}&g_tk=5381')
    d = d.text  # MusicJsonCallback(...)
    d = d[18:-1]
    return json.loads(d)


def getQQMusicDownloadLinkV1(filename, songmid):
    url = 'https://u.y.qq.com/cgi-bin/musicu.fcg'
    data = {"comm": {"ct": "19", "cv": "1777"},
            "queryvkey": {"method": "CgiGetVkey", "module": "vkey.GetVkeyServer", "param": {
                "uin": "",
                "guid": "QiuChenly",
                "referer": "y.qq.com",
                "songtype": [1],
                "filename": [filename],
                "songmid": [songmid]
            }}}
    d = getQQServersCallback(url, 1, data)
    d = d.json()
    vkey = d['queryvkey']['data']['midurlinfo'][0]
    return vkey


def getQQMusicSearch(key: str = "", page: int = 1) -> dict:
    """搜索音乐

    参数:
        key (str): 搜索关键词. 默认是 "".
        page (int): 分页序号. 默认是 1.

    返回值:
        dict: 返回搜索列表
    """
    # base url
    url = "https://u.y.qq.com/cgi-bin/musicu.fcg"
    # url = "https://u.y.qq.com/cgi-bin/musics.fcg" # 需要加密 懒得动了
    # base data content from qqmusic pc-client-apps

    # 一次获取最多获取50条数据 否则返回空列表
    page_per_num = 50

    data = {
        "comm": {
            "wid": "",
            "tmeAppID": "qqmusic",
            "authst": "",
            "uid": "",
            "gray": "0",
            "OpenUDID": "",
            "ct": "6",
            "patch": "2",
            "psrf_qqopenid": "",
            "sid": "",
            "psrf_access_token_expiresAt": "",
            "cv": "80600",
            "gzip": "0",
            "qq": "963084062",
            "nettype": "2",
            "psrf_qqunionid": "",
            "psrf_qqaccess_token": "",
            "tmeLoginType": "2"
        },
        "music.search.SearchCgiService.DoSearchForQQMusicDesktop": {
            "module": "music.search.SearchCgiService",
            "method": "DoSearchForQQMusicDesktop",
            "param": {
                "num_per_page": page_per_num,
                "page_num": page,
                "remoteplace": "txt.mac.search",
                "search_type": 0,
                "query": key,
                "grp": 1,
                "searchid": "BBC0673E-0B53-4B25-8EFF-QiuChenly",
                "nqc_flag": 0
            }
        }}

    res = getQQServersCallback(url, 1, data)
    # print(res.text)
    jsons = res.json()
    # 开始解析QQ音乐的搜索结果
    res = jsons['music.search.SearchCgiService.DoSearchForQQMusicDesktop']['data']
    list = res['body']['song']['list']
    meta = res['meta']

    # 数据清洗,去掉搜索结果中多余的数据
    list_clear = []
    for i in list:
        list_clear.append({
            'album': i['album'],
            'docid': i['docid'],
            'id': i['id'],
            'mid': i['mid'],
            'name': i['title'],
            'singer': i['singer'],
            'time_public': i['time_public'],
            'title': i['title'],
            'file': i['file'],
        })

    # rebuild json
    # list_clear: 搜索出来的歌曲列表
    # {
    #   size 搜索结果总数
    #   next 下一搜索页码 -1表示搜索结果已经到底
    #   cur  当前搜索结果页码
    # }
    return list_clear, {
        'size': meta['sum'],
        'next': meta['nextpage'],
        'cur': meta['curpage']
    }


def getQQMusicFileName(code, mid, format):
    """获取"""
    return f'{code}{mid}.{format}'


def getQQMusicDownloadLinkByMacApp(filename, songmid) -> dict:
    """从Macos客户端中获取的查询文件purl的接口

    参数:
        filename (str): 拼接好的文件名
        songmid (str): 原始服务器返回的mid信息

    返回值:
        data: 一个数据结构 包含了purl等信息 通过['purl']拿到下载地址
    """
    url = "https://u.y.qq.com/cgi-bin/musicu.fcg"
    data = {
        "comm": {
            "wid": "",
            "tmeAppID": "qqmusic",
            "authst": "",
            "uid": "",
            "gray": "0",
            "OpenUDID": "",
            "ct": "6",
            "patch": "2",
            "psrf_qqopenid": "",
            "sid": "",
            "psrf_access_token_expiresAt": "1682778170",
            "cv": "80600",
            "gzip": "0",
            "qq": "",
            "nettype": "2",
            "psrf_qqunionid": "",
            "psrf_qqaccess_token": "",
            "tmeLoginType": "2"
        },
        "queryvkey": {
            "module": "music.vkey.GetEDownUrl",
            "method": "CgiGetEDownUrl",
            "param": {
                "songmid": [songmid],
                "uin": "",
                # "musicfile": ["O6M0003dPNx22qGzZu.mgg"],
                "checklimit": 1,
                "scene": 0,
                "filename": [filename],
                "ctx": 1,
                "referer": "y.qq.com",
                "songtype": [1],
                "downloadfrom": 0,
                "nettype": "",
                "guid": "2d484d3157d4ed482e406e6c5fdcf8c3d3275deb"
            }
        }
    }
    res = getQQServersCallback(url, 1, data)
    res = res.json()
    return res["queryvkey"]["data"]["midurlinfo"][0]
