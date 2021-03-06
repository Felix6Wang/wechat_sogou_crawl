# -*- coding: utf-8 -*-
#查找公众号最新文章

# 导入包
from wechatsogou.tools import *
from wechatsogou import *
from PIL import Image
import datetime
import time
import logging
import logging.config

# 日志
logging.config.fileConfig('logging.conf')
logger = logging.getLogger()

# 搜索API实例
wechats = WechatSogouApi()

#数据库实例
mysql = mysql('mp_info')

#循环获取数据库中所有公众号
mysql.order_sql = " order by _id desc"
mp_list = mysql.find(0)
succ_count = 0

now_time = datetime.datetime.today()
now_time = datetime.datetime(now_time.year, now_time.month, now_time.day, 0, 0, 0)
#now_time = time.strftime("%Y-%m-%d %H:%M:%S",time.localtime(now_time))

for item in mp_list:
    try:
        time.sleep(1)
        #查看一下该号今天是否已经发送文章
        last_qunfa_id = item['last_qunfa_id']
        last_qunfa_time = item['last_qufa_time']
        if(last_qunfa_time and last_qunfa_time > now_time) :
            print("zhua guo le")
            continue #今天已经抓过了，不需要再重新抓了

        cur_qunfa_id = last_qunfa_id
        wz_url = ""
        if item.has_key('wz_url') :
            wz_url = item['wz_url']
        else :
            wechat_info = wechats.get_gzh_info(item['wx_hao'])
            if not wechat_info.has_key('url') :
                continue
            wz_url = wechat_info['url'];
            
        print(item['name'])
        
        #获取最近文章信息
        wz_list = wechats.get_gzh_message(url=wz_url)
        if u'链接已过期' in wz_list:
            wechat_info = wechats.get_gzh_info(item['wx_hao'])
            if not wechat_info.has_key('url') :
                continue
            print('guo qi sz chong xin huo qu success')
            wz_url = wechat_info['url'];
            wz_list = wechats.get_gzh_message(url=wz_url)
            mysql.table('mp_info').where({'_id':item['_id']}).save({'wz_url':wechat_info['url'],'logo_url':wechat_info['img'],'qr_url':wechat_info['qrcode']})
        #type==49表示是图文消息
        qunfa_time = ''
        for wz_item in wz_list :
            temp_qunfa_id = int(wz_item['qunfa_id'])
            if(last_qunfa_id >= temp_qunfa_id):
                break
            if(cur_qunfa_id < temp_qunfa_id):
                cur_qunfa_id = temp_qunfa_id
                qunfa_time = time.strftime("%Y-%m-%d %H:%M:%S",time.localtime(wz_item['datetime']))
            succ_count += 1
            if wz_item['type'] == '49':
                #把文章写入数据库
                #更新文章条数
                print(succ_count)
                print(wz_item['content_url'])
                if not wz_item['content_url'] :
                    continue
                time.sleep(1)
                article_info = wechats.deal_article(url=wz_item['content_url'])
                if not article_info :
                    continue
                if not article_info['comment'] :
                    continue
                sourceurl = wz_item['source_url']
                if len(sourceurl) >= 300 :
                    sourceurl = ''
                
                mysql.table('wenzhang_info').add({'title':wz_item['title'],
                                                'source_url':sourceurl,
                                                'content_url':article_info['yuan'],
                                                'cover_url':wz_item['cover'],
                                                'description':wz_item['digest'],
                                                'date_time': time.strftime("%Y-%m-%d %H:%M:%S",time.localtime(wz_item['datetime'])),
                                                'mp_id':item['_id'],
                                                'author':wz_item['author'],
                                                'msg_index':wz_item['main'],
                                                'copyright_stat':wz_item['copyright_stat'],
                                                'qunfa_id':wz_item['qunfa_id'],
                                                'type':wz_item['type'],
                                                'like_count':0,
                                                'read_count':0,
                                                'comment_count':0})

        #更新最新推送ID
        if(last_qunfa_id < cur_qunfa_id):
            mysql.table('mp_info').where({'_id':item['_id']}).save({'last_qunfa_id':cur_qunfa_id,'last_qufa_time':qunfa_time,'update_time':time.strftime("%Y-%m-%d %H:%M:%S",time.localtime(time.time()))})
    except KeyboardInterrupt:
        break
    # except: #如果不想因为错误使程序退出，可以开启这两句代码
    #     continue
            
print('success')