# -*- coding: utf-8 -*-
#  Copyright (c) 2023. 秋城落叶, Inc. All Rights Reserved
#  @作者         : 秋城落叶(QiuChenly)
#  @邮件         : 1925374620@qq.com
#  @文件         : 项目 [qqmusic] - main.py
#  @修改时间    : 2023-03-02 03:39:25
#  @上次修改    : 2023/3/2 上午3:39
import base64
import math
import requests
import os
import json
import threading

from src.Api.QQMusic import getQQMusicDownloadLinkByMacApp, getQQMusicDownloadLinkV1, getQQMusicMediaLyric, \
    getQQMusicSearch, getQQMusicFileName, getQQMusicLyricByMacApp, setQQCookie
from src.Types.Types import Songs

threadLock = threading.Lock()  # 多线程锁 防止同时创建同一个文件夹冲突


def clear():
    print('\033c', end='')


def downSingle(it):
    global download_home, onlyShowSingerSelfSongs, musicAlbumsClassification
    songmid = it['songmid']
    file = getQQMusicFileName(it['prefix'], it['mid'], it['extra'])
    musicid = it['musicid']
    link = getQQMusicDownloadLinkByMacApp(file, songmid)
    # link = getQQMusicDownloadLinkV1(file, songmid)  # 早期方法 可食用
    vkey = link['purl']

    musicFileInfo = f"{it['singer']} - {it['title']} [{it['notice']}] {round(int(it['size']) / 1024 / 1024, 2)}MB - {file}"

    # 测试歌词下载保存接口代码
    # lyric = getQQMusicMediaLyric(songmid) # 早期方法 已弃用
    # lyric = getQQMusicLyricByMacApp(musicid)
    # lyric = getQQMusicLyricByWeb(musicid)
    # lyrics = base64.b64decode(lyric['lyric'])
    # with open("lyric.txt", 'wb') as code:
    #     code.write(lyrics)
    #     code.flush()
    # 测试歌词下载代码结束

    if vkey == '':
        print(f"找不到资源文件! 解析歌曲下载地址失败！{musicFileInfo}")
        return False

    link = f'http://ws.stream.qqmusic.qq.com/{vkey}&fromtag=140'

    if link.find('qqmusic.qq.com') == -1:
        print(f"无法加载资源文件！解析歌曲下载地址失败！{musicFileInfo}")
        return False

    # prepare
    localFile = f"{it['singer']} - {it['title']}.{it['extra']}".replace(
        "/", "\\")
    localLrcFile = f"{it['singer']} - {it['title']}.lrc".replace(
        "/", "\\")
    mShower = localFile
    my_path = download_home + it['singer'] + '/'

    if not onlyShowSingerSelfSongs:
        if not os.path.exists(my_path):
            os.mkdir(f"{my_path}")

    threadLock.acquire()  # 多线程上锁解决同时创建一个mkdir的错误
    my_path = f"{my_path}{it['album'] if musicAlbumsClassification else ''}"

    try:
        if not os.path.exists(my_path):
            os.mkdir(f"{my_path}")
    except:
        pass
    threadLock.release()
    localFile = os.path.join(my_path, f"{localFile}")
    localLrcFile = os.path.join(my_path, f"{localLrcFile}")

    # 下载歌词
    if not os.path.exists(localLrcFile):
        print(f"本地歌词文件不存在,准备自动下载: [{localLrcFile}].")
        # lyric = getQQMusicMediaLyric(songmid)  # lyric trans
        lyric = getQQMusicLyricByMacApp(musicid)
        if lyric['lyric'] != '':
            # "retcode": 0,
            # "code": 0,
            # "subcode": 0,
            # {'retcode': -1901, 'code': -1901, 'subcode': -1901}
            # 外语歌曲有翻译 但是👴不需要！
            lyric = base64.b64decode(lyric['lyric'])
            with open(localLrcFile, 'wb') as code:
                code.write(lyric)
                code.flush()
        else:
            print(f"歌词获取失败!服务器上搜索不到此首 [{it['singer']} - {it['title']}] 歌曲歌词!")

    # 下载歌曲
    if os.path.exists(localFile):
        if os.path.getsize(localFile) == int(it['size']):
            print(f"本地已下载,跳过下载 [{it['album']} / {mShower}].")
            return True
        else:
            print(
                f"本地文件尺寸不符: {os.path.getsize(localFile)}/{int(it['size'])},开始覆盖下载 [{mShower}].")
    print(f'正在下载 | {it["album"]} / {musicFileInfo}')
    f = requests.get(link)
    with open(localFile, 'wb') as code:
        code.write(f.content)
        code.flush()

    return True


def fixWindowsFileName2Normal(texts=''):
    """
    修正windows的符号问题
    “?”、“、”、“╲”、“/”、“*”、““”、“”“、“<”、“>”、“|” " " ":"

    参数:
        texts (str, optional): 通常类型字符串. 默认值为 ''.

    返回值:
        str: 替换字符后的结果
    """
    targetChars = {
        '|': ',',
        '/': ' - ',
        '╲': ' - ',
        '、': '·',
        '“': '"',
        '”': '"',
        '*': 'x',
        '?': '？',  # fix for sample: Justin Bieber - What do you mean ? (Remix)
        '<': '《',
        '>': '》',
        ' ': '',
    }
    for suffix in targetChars:
        fix = targetChars[suffix]
        texts = texts.replace(suffix, fix)
    return texts


def needFilter(fileName=''):
    """
    检查是否需要过滤本首歌曲

    """
    global filterList
    for it in filterList:
        if fileName.upper().find(it.upper()) != -1:
            return True
    return False


def parseList(mlist, target):
    """
    处理音乐列表
    如果需要屏蔽显示某些类型的歌曲，可以在这个函数里末尾处理

    Args:
        list (Array<T>): 歌曲列表
        target (str): 搜索的歌手名称,用于是否使用歌手名匹配歌曲歌手信息

    Returns:
        lists, songs: 处理过的数据数组
    """
    add = 1
    span = "  "
    songs: list[Songs] = []
    lists = []
    for i in mlist:
        singer = i['singer'][0]['name']
        # print(json.dumps(i['singer']))
        if singer != target and onlyShowSingerSelfSongs:
            # print(f"{singer} not is {target}")
            continue
        if add > 9:
            span = " "
        if add > 99:
            span = ""

        id = i["file"]
        # 批量下载不需要选择音质 直接开始解析为最高音质 枚举
        code = ""
        format = ""
        qStr = ""
        fsize = 0
        mid = id['media_mid']
        if int(id['size_hires']) != 0:
            # 高解析无损音质
            code = "RS01"
            format = "flac"
            qStr = "高解析无损 Hi-Res"
            fsize = int(id['size_hires'])
        elif int(id['size_flac']) != 0:
            isEnc = False  # 这句代码是逆向出来的 暂时无效
            if (isEnc):
                code = "F0M0"
                format = "mflac"
            else:
                code = "F000"
                format = "flac"
            qStr = "无损品质 FLAC"
            fsize = int(id['size_flac'])
        elif int(id['size_320mp3']) != 0:
            code = "M800"
            format = "mp3"
            qStr = "超高品质 320kbps"
            fsize = int(id['size_320mp3'])
        elif int(id['size_192ogg']) != 0:
            isEnc = False  # 这句代码是逆向出来的 暂时无效
            if (isEnc):
                code = "O6M0"
                format = "mgg"
            else:
                code = "O600"
                format = "ogg"
            qStr = "高品质 OGG"
            fsize = int(id['size_192ogg'])
        elif int(id['size_128mp3']) != 0:
            isEnc = False  # 这句代码是逆向出来的 暂时无效
            if (isEnc):
                code = "O4M0"
                format = "mgg"
            else:
                code = "M500"
                format = "mp3"
            qStr = "标准品质 128kbps"
            fsize = int(id['size_128mp3'])
        elif int(id['size_96aac']) != 0:
            code = "C400"
            format = "m4a"
            qStr = "低品质 96kbps"
            fsize = int(id['size_96aac'])
        else:
            print("这首歌曲好像无法下载,请检查是否有vip权限.")
            return False

        albumName = str(i["album"]['title']).strip(" ")
        if albumName == '':
            albumName = "未分类专辑"

        # 开始检查歌曲过滤显示
        # 第三方修改歌曲可以在这里对歌曲做二次处理
        flacName = fixWindowsFileName2Normal(f'{i["title"]}')

        if needFilter(flacName):
            # print(f'过滤歌曲: {flacName}')
            continue

        # 通过检查 将歌曲放入歌曲池展示给用户 未通过检查的歌曲将被放弃并且不再显示
        songs.append({
            'prefix': code,
            'extra': format,
            'notice': qStr,
            'mid': mid,
            'musicid': i['id'],
            'songmid': i['mid'],
            'size': fsize,
            'title': flacName,
            'singer': fixWindowsFileName2Normal(f'{singer}'),
            'album': fixWindowsFileName2Normal(albumName)}
        )

        time_publish = i["time_public"]
        if time_publish == '':
            time_publish = "1970-01-01"
        lists.append(
            f'{add} {span}{time_publish} {singer} - {i["title"]} | {qStr}')
        add += 1
    # 这部分其实可以只返回songs 但是代码我懒得改了 反正又不是不能用=v=
    return lists, songs


def downAll(target, size):
    """
    一键下载所有搜索结果
    """
    num = math.ceil(size / 100)
    result = []
    for i in range(1, num + 1):
        (list, meta) = getQQMusicSearch(target, i)
        list, songs = parseList(list, target)
        result.extend(songs)
    return result


def _main(target=""):
    """
    主函数 不建议随意修改 请在上方函数修改
    """
    global download_home, dualThread, searchKey, onlyShowSingerSelfSongs, musicAlbumsClassification

    # fix create directory files error(if not exists)
    if not os.path.exists(download_home):
        os.mkdir(f"{download_home}")

    # 当关闭仅搜索歌手模式的时候 此处代码不应执行
    my_path = f'{download_home}{target + "/" if onlyShowSingerSelfSongs else ""}'
    if onlyShowSingerSelfSongs and not os.path.exists(my_path):
        os.mkdir(f"{my_path}")

    # 根据文件名获取下载链接
    # getDownloadLink("RS01003w2xz20QlUZt.flac")

    # filename = "ID9TZr-ensC/-rJ2t6-atFsm+sRG+2S6CqS"
    # filename = decryptText(filename, qq)
    # 解密后 RS01 003w2xz20QlUZt . flac
    page = 1
    while True:
        (lst, meta) = getQQMusicSearch(target, page)
        lst, songs = parseList(lst, target)
        while True:
            clear()
            print(
                "==== Welcome to Digit High Quality Music Download Center $$ Creative By QiuChenly ====\n")
            for li in lst:
                print(li)
            willDownAll = False
            print(f"""
==== 获取列表成功.共{meta['size']}条搜索结果,当前第{page}页,{'下一页仍有更多数据' if meta['next'] != -1 else '下一页没有数据了'}. ====

n 切换下一页 (Next)
p 切换上一页 (Previous)
l 一键下载所有歌曲 (All)
a 一键下载本页所有歌曲 (All)
1 <如: 1> 若要下载某一首,请输入歌曲前方的序号 (Single)
s [{searchKey}] 修改搜索关键词 (Search)
t [{dualThread}] 修改当前线程并发. (Thread)
h 修改当前下载缓存的主目录 [{download_home}] (Download Home)
o [{'已开启' if onlyShowSingerSelfSongs else '已关闭'}] 切换模式:仅显示搜索的歌手歌曲 (OnlyMatchSinger&Songer)
c [{'已开启' if musicAlbumsClassification else '已关闭'}] 切换模式:按照专辑名称分文件夹归档音乐歌曲文件 (Music Albums Classification)

==== 请在下方输入指令 ====
>""", end='')
            inputKey = input()
            if inputKey == "n":
                break
            if inputKey == "o":
                onlyShowSingerSelfSongs = not onlyShowSingerSelfSongs
                saveConfigs()
                return _main(searchKey)
            elif inputKey == "s" or inputKey == "h":
                print(
                    f"请输入新的{'搜索关键词' if inputKey == 's' else '下载主目录'}:", end='')
                if inputKey == 'h':
                    download_home = input()
                    download_home = download_home.replace(' ', '')
                    if not download_home.endswith('/'):
                        download_home += '/'
                else:
                    searchKey = input()
                saveConfigs()
                _main(searchKey)
                return
            elif inputKey == 'a':
                # 下载本页所有歌曲
                willDownAll = True
            elif inputKey == 'l':
                songs = downAll(target, meta['size'])
                willDownAll = True
            elif inputKey == 't':
                print("请输入线程数:", end='')
                dualThread = int(input())
                saveConfigs()
                continue
            elif inputKey == 'c':
                musicAlbumsClassification = not musicAlbumsClassification
                saveConfigs()
                continue
            elif inputKey == 'p':
                page -= 2
                if page + 1 < 1:
                    page = 0
                break
            if willDownAll:
                thList = []
                for mp3 in songs:
                    th = threading.Thread(target=downSingle, args=(mp3,))
                    thList.append(th)
                    th.start()
                    if len(thList) == dualThread:
                        while len(thList) > 0:
                            thList.pop().join()
                while len(thList) > 0:
                    thList.pop().join()
                willDownAll = False
            else:
                op = -1
                try:
                    op = int(inputKey)
                except:
                    print("输入无效字符,请重新输入。")
                    continue
                it = songs[op - 1]
                downSingle(it)
            print("下载完成!")
        page += 1


def saveConfigs():
    """
    保存设置
    """
    cfg = json.dumps({
        'dualThread': dualThread,
        'download_home': download_home,
        'searchKey': searchKey,
        'onlyShowSingerSelfSongs': onlyShowSingerSelfSongs,
        'musicAlbumsClassification': musicAlbumsClassification,
        'filterList': filterList
    }, ensure_ascii=False).encode()
    with open(cfgName, "wb") as cf:
        cf.write(cfg)
        cf.flush()


download_home = ""
"""
下载的文件要保存到哪里(目录) /Volumes/data类似于windows上的C:/
    
就是你自定义的文件夹名称 随便指定 会自动创建

本参数已自动处理 不建议修改
"""

dualThread = 5
"""
多线程下载 线程数量
#####  如果你的宽带>=1000Mbps 可以适当调整至64
#####  100Mbps左右的小宽带不建议调高 会导致带宽不足连接失败
"""

searchKey = "周杰伦"
"""
默认搜索Key
"""

onlyShowSingerSelfSongs = False
"""
###  搜索歌曲名称时是否强制指定歌手和搜索key一致，用于过滤非本歌手的歌曲
如果是False,则显示所有搜索结果 如果你只想搜索某个歌手则可以开启本选项 默认关闭
#### 如何理解本选项？ 搜索结果是按照[时间] [歌手] - [歌名]排序的，你搜索的关键词searchKey严格匹配[歌手]选项,不是你搜索的歌手的歌则会强制过滤显示，如果你需要切换显示模式则输入 o 即可显示搜索未过滤结果
"""

musicAlbumsClassification = True
"""
音乐文件自动归档到单独的专辑文件夹中,如果关闭那么就不会生成专辑目录,默认自动按照专辑名称分类归档音乐文件
"""

cfgName = "config.json"
"""
配置项名称
"""


def initEnv():
    """
    第一次使用初始化环境信息 可以删除config.json，会自动创建初始化。
    """
    global download_home
    download_home = os.getcwd() + '/music/'  # 自动定位到执行目录，兼容Windows默认配置。
    saveConfigs()


filterList = ['DJ', 'Live', '伴奏', '版)', '慢四']
"""
关键词过滤数组 注意 英文字母自动upper到大写比对 所以只需要写一次即可 如 DJ Dj 只需要写 ‘DJ’即可 自动到大写比对 
"""

# 初次使用即保存配置项
if not os.path.exists(cfgName):
    initEnv()

# read default config
with open(cfgName, encoding='utf-8') as cfg:
    cfgLst = cfg.read()
    params = json.loads(cfgLst)
    download_home = params['download_home']
    onlyShowSingerSelfSongs = bool(params['onlyShowSingerSelfSongs'])
    searchKey = params['searchKey']
    dualThread = int(params['dualThread'])
    musicAlbumsClassification = params['musicAlbumsClassification']
    filterList = params['filterList']

    # 修复 删除了本地目录后缓存中的本地目录后，下次执行代码则还会去读这个目录 不存在导致FileNotFoundError: [Errno 2] No such file or directory错误
    if not os.path.exists(download_home):
        initEnv()

print("请输入Cookie(扫码登录网页版qq音乐随便复制个请求的Cookie就可以): ")
Cookie = input()
setQQCookie(Cookie)
_main(searchKey)
