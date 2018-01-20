# -*- coding: UTF-8 -*-

import json
import os

def get_Friends_list():
    k = 0
    file_list=[i for i in os.listdir('./friends/') if i.endswith('json')]
    friends_list=[]
    for f in file_list:
        with open('./friends/{}'.format(f),'r',encoding='utf-8') as w:
            data=w.read()[95:-5]
            js=json.loads(data)
            # print(js)
            for i in js:
                k+=1
                friends_list.append(i['data'])
    return friends_list


friends_list=get_Friends_list()
# print(friends_list)

# if friends_list.__contains__("947948366"):
#     print("666")


