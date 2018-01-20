# -*- coding: UTF-8 -*-

from  selenium import webdriver
import requests
import time
import os
from urllib import parse
import configparser
from socket import timeout

class Crawler(object):

    # 初始化浏览器信息和账户信息
    def __init__(self):
        self.web = webdriver.Chrome()  # 模拟Chrome
        self.web.get('https://user.qzone.qq.com')
        config = configparser.ConfigParser(allow_no_value=False)
        config.read('userinfo.ini')
        self.__username = config.get('qq_info', 'qq_number')
        self.__password = config.get('qq_info', 'qq_password')
        self.headers = {
            'host': 'h5.qzone.qq.com',
            'accept-encoding': 'gzip, deflate, br',
            'accept-language': 'zh-CN,zh;q=0.8',
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/59.0.3071.115 Safari/537.36',
            'connection': 'keep-alive'
        }
        self.request = requests.Session()
        self.cookies = {}
        self.g_tk = ""
        self.g_qzonetoken = ""
        self.counts = 0  # 计数器
        self.sum = 0 # 好友数量
        self.friendList = []

    # 模拟登录
    def login(self):
        self.web.switch_to.frame('login_frame')
        log = self.web.find_element_by_id("switcher_plogin")
        log.click()
        time.sleep(1)
        username = self.web.find_element_by_id('u')
        username.send_keys(self.__username)
        ps = self.web.find_element_by_id('p')
        ps.send_keys(self.__password)
        btn = self.web.find_element_by_id('login_button')
        time.sleep(1)
        btn.click()
        time.sleep(2)
        self.web.get('https://user.qzone.qq.com/{}'.format(self.__username))
        cookie = ''
        for elem in self.web.get_cookies():
            cookie += elem["name"] + "=" + elem["value"] + ";"
        self.cookies = cookie
        self.get_g_tk()
        self.headers['Cookie'] = self.cookies  # 拿到Cookie



    # QQ空间g_tk加密算法破解
    def get_g_tk(self):
        p_skey = self.cookies[self.cookies.find('p_skey=') + 7: self.cookies.find(';', self.cookies.find('p_skey='))]
        h = 5381
        for i in p_skey:
            h += (h << 5) + ord(i)
        # print('g_tk', h & 2147483647)
        self.g_tk = h & 2147483647


    # 好友列表前部分路径
    def get_friends_url(self):
        url='https://h5.qzone.qq.com/proxy/domain/base.qzone.qq.com/cgi-bin/right/get_entryuinlist.cgi?'
        params = {"uin": self.__username,
              "fupdate": 1,
              "action": 1,
              "g_tk": self.g_tk}
        url = url + parse.urlencode(params)
        return url


    # 将好友列表写到json文件中
    def get_friends_num(self):
        t=True
        offset=0
        url=self.get_friends_url()
        while t:
            url_=url+'&offset='+str(offset)
            page=self.request.get(url=url_,headers=self.headers)
            if "\"uinlist\":[]" in page.text:
                t=False
            else:
                w = open('./friends/' + str(offset) +'.json','w', encoding='utf-8')
                w.write(page.text)
                offset += 50



    # 说说url前半部分路径
    def get_shuoshuo_url(self):
        url = 'https://h5.qzone.qq.com/proxy/domain/taotao.qq.com/cgi-bin/emotion_cgi_msglist_v6?'
        params = {
            "sort": 0,
            "start": 0,
            "num": 20,
            "cgi_host": "http://taotao.qq.com/cgi-bin/emotion_cgi_msglist_v6",
            "replynum": 100,
            "callback": "_preloadCallback",
            "code_version": 1,
            "inCharset": "utf-8",
            "outCharset": "utf-8",
            "notice": 0,
            "format": "jsonp",
            "need_private_comment": 1,
            "g_tk": self.g_tk
        }
        url = url + parse.urlencode(params)
        return url





    # 爬好友主方法
    def crawlerFriends(self):
        from getFriends import friends_list
        self.friendList = friends_list
        self.sum = friends_list.__len__() # 已经爬了sum个好友
        for u in friends_list:
            try:
                QQ_number = u
                print("开始爬取好友", QQ_number, "的数据")

                # 爬取个人资料
                self.web.get('https://user.qzone.qq.com/' + QQ_number)
                # QQ空间g_qzonetoken参数获取
                self.g_qzonetoken = self.web.execute_script("return window.g_qzonetoken")
                time.sleep(0.2)  # 防止封号
                url = "https://h5.qzone.qq.com/proxy/domain/base.qzone.qq.com/cgi-bin/user/cgi_userinfo_get_all?uin=#targerQQ#&vuin=#myQQ#&fupdate=1&rd=0.8804774685477361&g_tk=#gtk#&qzonetoken=#qzonetoken#"
                url = url.replace('#gtk#', str(self.g_tk)).replace('#qzonetoken#', str(self.g_qzonetoken)).replace(
                    '#targerQQ#', QQ_number).replace('#myQQ#', self.__username)
                ziliao_detail = self.request.get(url=url, headers=self.headers)
                time.sleep(0.2)  # 防止封号

                # 自动跳转回来的如 000000000
                # 未开通空间的如   999999999
                # 404跳转小孩儿的  000000001
                # 没有权限的如     275893874
                # 正常能访问到的   947948366
                # 有提问的如         000010012
                if ("无权访问" in ziliao_detail.text) or ("非法操作" in ziliao_detail.text):
                    print("没有权限爬取", QQ_number, "将爬取下一个qq")
                    time.sleep(0.4)
                    continue

                # 将个人资料写入json文件
                if not os.path.exists("./friendsdata/" + QQ_number):
                    os.mkdir("friendsdata/" + QQ_number)
                if not os.path.exists("./friendsdata/" + QQ_number + "/info/"):
                    os.mkdir("friendsdata/" + QQ_number + "/info/")
                with open('./friendsdata/' + QQ_number + "/info/" + QQ_number + '.json', 'w',
                          encoding='utf-8') as w:
                    w.write(ziliao_detail.text)

                # 爬取个人说说
                url = self.get_shuoshuo_url()
                t = True
                url_ = url + '&uin=' + QQ_number
                pos = 0
                while t:
                    url__ = url_ + '&pos=' + str(pos)
                    shuoshuo_detail = self.request.get(url=url__, headers=self.headers)
                    time.sleep(0.2)  # 防止封号
                    if "\"msglist\":null" in shuoshuo_detail.text or "\"message\":\"没有权限\"" in shuoshuo_detail.text:
                        t = False

                    # 将个人说说写入json文件
                    else:
                        if not os.path.exists("./friendsdata/" + QQ_number):
                            os.mkdir("friendsdata/" + QQ_number)
                        if not os.path.exists("./friendsdata/" + QQ_number + "/shuoshuo/"):
                            os.mkdir("friendsdata/" + QQ_number + "/shuoshuo/")
                        with open('./friendsdata/' + QQ_number + "/shuoshuo/" + str(pos) + '.json', 'w',
                                  encoding='utf-8') as w:
                            w.write(shuoshuo_detail.text)
                        pos += 20
                        time.sleep(0.2)  # 防止封号

                # 爬取个人访客
                self.web.get('https://user.qzone.qq.com/' + QQ_number)
                self.g_qzonetoken = self.web.execute_script("return window.g_qzonetoken")
                time.sleep(0.2)  # 防止封号
                url = "https://h5.qzone.qq.com/proxy/domain/g.qzone.qq.com/cgi-bin/friendshow/cgi_get_visitor_simple?uin=#targerQQ#&mask=2&g_tk=#gtk#&page=1&fupdate=1&qzonetoken=#qzonetoken#"
                url = url.replace('#gtk#', str(self.g_tk)).replace('#qzonetoken#', str(self.g_qzonetoken)).replace(
                    '#targerQQ#', QQ_number)
                time.sleep(0.2)  # 防止封号
                visit_detail = self.request.get(url=url, headers=self.headers)

                # 将访客信息写入json文件
                if not os.path.exists("./friendsdata/" + QQ_number):
                    os.mkdir("friendsdata/" + QQ_number)
                if not os.path.exists("./friendsdata/" + QQ_number + "/visit/"):
                    os.mkdir("friendsdata/" + QQ_number + "/visit/")
                with open('./friendsdata/' + QQ_number + "/visit/" + QQ_number + '.json', 'w',
                          encoding='utf-8') as w:
                    w.write(visit_detail.text)

                # 该qq爬取完毕
                print("成功爬取", QQ_number, "数据")
                time.sleep(0.5)  # 防止封号

            except IOError:
                print("ioerror")
                continue
            except Exception:
                print("exception")
                continue
            except timeout:
                print("timeout")
                continue
            except:
                print("others")
                continue



    # 爬陌生人主方法
    def crawlerOthers(self):

        # 计数器，爬取4000停止
        self.counts = self.sum
        for qq in range(99999999, 1100000000):
            try:
                QQ_number = str(qq)
                if QQ_number in self.friendList:  # 去重
                    continue
                print("开始爬取",QQ_number,"的数据")

                # 爬取个人资料
                self.web.get('https://user.qzone.qq.com/' + QQ_number)
                # QQ空间g_qzonetoken参数获取
                self.g_qzonetoken = self.web.execute_script("return window.g_qzonetoken")
                time.sleep(0.2) # 防止封号
                url = "https://h5.qzone.qq.com/proxy/domain/base.qzone.qq.com/cgi-bin/user/cgi_userinfo_get_all?uin=#targerQQ#&vuin=#myQQ#&fupdate=1&rd=0.8804774685477361&g_tk=#gtk#&qzonetoken=#qzonetoken#"
                url = url.replace('#gtk#', str(self.g_tk)).replace('#qzonetoken#', str(self.g_qzonetoken)).replace(
                    '#targerQQ#', QQ_number).replace('#myQQ#', self.__username)
                ziliao_detail = self.request.get(url=url, headers=self.headers)
                time.sleep(0.2) # 防止封号

                # 自动跳转回来的如 000000000
                # 未开通空间的如   999999999
                # 404跳转小孩儿的  000000001
                # 没有权限的如     275893874
                # 正常能访问到的   947948366
                # 有提问的如       000010012
                if ("无权访问" in ziliao_detail.text) or ("非法操作" in ziliao_detail.text):
                    print("没有权限爬取",QQ_number,"将爬取下一个qq")
                    time.sleep(0.4)
                    continue

                # 将个人资料写入json文件
                if not os.path.exists("./othersdata/" + QQ_number):
                    os.mkdir("othersdata/" + QQ_number)
                if not os.path.exists("./othersdata/" + QQ_number + "/info/"):
                    os.mkdir("othersdata/" + QQ_number + "/info/")
                with open('./othersdata/' + QQ_number + "/info/" + QQ_number + '.json', 'w',
                          encoding='utf-8') as w:
                    w.write(ziliao_detail.text)


                # 爬取个人说说
                url = self.get_shuoshuo_url()
                t = True
                url_ = url + '&uin=' + QQ_number
                pos = 0
                while t:
                    url__ = url_ + '&pos=' + str(pos)
                    shuoshuo_detail = self.request.get(url=url__, headers=self.headers)
                    time.sleep(0.2) # 防止封号
                    if "\"msglist\":null" in shuoshuo_detail.text or "\"message\":\"没有权限\"" in shuoshuo_detail.text:
                        t = False

                    # 将个人说说写入json文件
                    else:
                        if not os.path.exists("./othersdata/" + QQ_number):
                            os.mkdir("othersdata/" + QQ_number)
                        if not os.path.exists("./othersdata/" + QQ_number + "/shuoshuo/"):
                            os.mkdir("othersdata/" + QQ_number + "/shuoshuo/")
                        with open('./othersdata/' + QQ_number + "/shuoshuo/" + str(pos) + '.json', 'w',
                                  encoding='utf-8') as w:
                            w.write(shuoshuo_detail.text)
                        pos += 20
                        time.sleep(0.2) # 防止封号


                # 爬取个人访客
                self.web.get('https://user.qzone.qq.com/' + QQ_number)
                self.g_qzonetoken = self.web.execute_script("return window.g_qzonetoken")
                time.sleep(0.2) # 防止封号
                url = "https://h5.qzone.qq.com/proxy/domain/g.qzone.qq.com/cgi-bin/friendshow/cgi_get_visitor_simple?uin=#targerQQ#&mask=2&g_tk=#gtk#&page=1&fupdate=1&qzonetoken=#qzonetoken#"
                url = url.replace('#gtk#', str(self.g_tk)).replace('#qzonetoken#', str(self.g_qzonetoken)).replace(
                    '#targerQQ#', QQ_number)
                time.sleep(0.2) # 防止封号
                visit_detail = self.request.get(url=url, headers=self.headers)

                # 将访客信息写入json文件
                if not os.path.exists("./othersdata/" + QQ_number):
                    os.mkdir("othersdata/" + QQ_number)
                if not os.path.exists("./othersdata/" + QQ_number + "/visit/"):
                    os.mkdir("othersdata/" + QQ_number + "/visit/")
                with open('./othersdata/' + QQ_number + "/visit/" + QQ_number + '.json', 'w',
                          encoding='utf-8') as w:
                    w.write(visit_detail.text)

                # 该qq爬取完毕
                print("成功爬取",QQ_number,"数据,第",self.counts,"个")
                self.counts = self.counts + 1
                time.sleep(0.5) # 防止封号
                if(self.counts>=8000): # 每人爬4000
                    print("所有数据爬取完毕！")
                    break

            except IOError:
                print("ioerror")
                continue
            except Exception:
                print("exception")
                continue
            except timeout:
                print("timeout")
                continue
            except:
                print("others")
                continue



if __name__ == '__main__':
    cbw = Crawler()
    cbw.login()
    cbw.get_friends_num()
    cbw.crawlerFriends()
    cbw.crawlerOthers()
