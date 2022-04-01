import re
import csv
import time
import json
import os
import pandas
import requests
from random import randint
from tenacity import retry, stop_after_attempt


class Taobao_Comments:
    def __init__(self):
        self.save_path = 'comments.csv'
        #xlsx与上一个文件衔接不连贯，最好csv
        self.read_path = 'taobao_search.xlsx'

        self.tmall_comments_url = 'https://rate.tmall.com/list_detail_rate.htm'
        self.taobao_comments_url = 'https://rate.taobao.com/feedRateList.htm'

        self.sleep_time = 3

        self.tmall_cookike = 'cna=KHjMGq2e1FQCASdEl6OijsaN; sca=67329b3a; tbsa=b0c4422a2479428794ed9d5c_1648726364_2'
        self.tmall_ua = '098#E1hv4vvnvPyvUvCkvvvvvjiWR2LOAjY8R2qOljD2PmPWsj1Rn2ch6j3PRL5ZgjlR9vhv2nMSbFQp7rMNzskrz8QCvCBboZgWg9CvolQ7Npyt+mt8vccBA4OCvvBvpvpZmvhvLhUXjQmFejwuNZuQD40OJoBYcgkQ+ul1BC69Qbm655XPwZeQ0fJ6EvBQog0HKfE9Z5IUDaVTRogREcqvaXgOfvxYorsv5CO07oDn9WmUvpvVpyUUCEAwuvhvmhCvCPz+x0PJKvhv8hCvvvvvvhCvphvwv9vvpJHvpCQmvvChNhCvjvUvvhBZphvwv9vvBHpvvpvVph9vvvvv29hvCvvvMMGgvpvhphvvvUOCvvBvppvvdvhvmZC28BvhvhCVTs9CvvBvpvvv'

    @retry(stop=stop_after_attempt(3))
    def parse_tmall(self, url, item_id, seller_id, title, product_pic):
        """ 获取SPUID 过后才能获取评论 """

        # 获取 SPUID
        headers = {
            'referer': 'https://s.taobao.com/',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/99.0.4844.84 Safari/537.36',
            'cookie': self.tmall_cookike
        }

        try:
            response = requests.get(url, headers=headers, timeout=10)

        except:
            print("请求超时！重连中！")

            time.sleep(self.sleep_time)
            raise Exception

        spuid = re.search('"spuId":"(.*?)",', response.text).group(1)

        time.sleep(self.sleep_time)

        # 获取评论
        headers = {
            'referer': url,
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/99.0.4844.84 Safari/537.36',
            'cookie': self.tmall_cookike
        }

        params = {
            'itemId': item_id,
            'spuId': spuid,
            'sellerId': seller_id,
            'order': '3',
            'currentPage': '1',
            'append': '0',
            'content': '1',
            'tagId': '',
            'posi': '',
            'picture': '',
            'groupId': '',
            'ua': self.tmall_ua,
            'needFold': '0',
            '_ksTS': str(time.time() * 1000).replace('.', '_')[0:17],
            'callback': 'jsonp464'
        }

        try:

            response_comment = requests.get(self.tmall_comments_url, params=params, headers=headers, timeout=10)

        except:
            print("请求超时！重连中！")

            time.sleep(self.sleep_time)
            raise Exception
        json_content = json.loads(re.search(r'jsonp464\((.*?)}}\)', response_comment.text).group(1) + "}}")

        max_page = self.parse_tmall_comments(json_content, url, item_id, seller_id, title, product_pic, headers, params)

        if max_page > 1:
            time.sleep(self.sleep_time)
            for page in range(2, int(max_page + 1)):
#            for page in range(2, 2):
                self.parse_tmall_next_page(page, url, item_id, seller_id, spuid, title, product_pic)
                time.sleep(self.sleep_time)

        else:
            return True

    @retry(stop=stop_after_attempt(3))
    def parse_tmall_next_page(self, page, url, item_id, seller_id, spuid, title, product_pic):
        headers = {
            'referer': url,
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/99.0.4844.84 Safari/537.36',
            'cookie': self.tmall_cookike
        }

        params = {
            
            'itemId': item_id,
            'spuId': spuid,
            'sellerId': seller_id,
            'order': '3',
            'currentPage': page,
            'append': '0',
            'content': '1',
            'tagId': '',
            'posi': '',
            'picture': '',
            'groupId': '',
            'ua': self.tmall_ua,
            'needFold': '0',
            '_ksTS': str(time.time() * 1000).replace('.', '_')[0:17],
            'callback': 'jsonp464'
        }

        try:
            response_comment = requests.get(self.tmall_comments_url, params=params, headers=headers, timeout=10)

        except:
            print("请求超时，重连中！")

            time.sleep(self.sleep_time)
            raise Exception

        json_content = json.loads(re.search(r'jsonp464\((.*?)}}\)', response_comment.text).group(1) + "}}")

        self.parse_tmall_comments(json_content, url, item_id, seller_id, title, product_pic, headers, params)

    def parse_tmall_comments(self, json_content, url, item_id, seller_id, title, product_pic, headers, params):
        comments_list = json_content['rateDetail']['rateList']
        for comments in comments_list:
            username = comments['displayUserNick']
            comments_id = comments['id']
            content = comments['rateContent']

            pic_url_list = comments['pics']
            if len(pic_url_list) == 0:
                pic_result = "空"

            else:
                pic_result = []
                for pic in pic_url_list:
                    ###########
                    save_path_pic='D:/买家图片/'
                    if not os.path.exists(save_path_pic):
                        os.makedirs(save_path_pic)
                    ranstr=randint(0,9999999)
                    ranstr=str(ranstr)
                    with open(save_path_pic.rstrip('/')+'/'+ranstr+pic[-4:].replace('/',''),'wb') as f:
                        img_get=requests.get('https:'+pic, params=params, headers=headers, timeout=10).content
                        f.write(img_get)
                    ###########
                    pic_result.append('https:' + pic)

            comments_date = comments['rateDate']

            result = [url, item_id, seller_id, title, product_pic, username, comments_id, content, pic_result, comments_date]
            self.save_to_csv(result)

        max_page = json_content['rateDetail']['paginator']['lastPage']
        if max_page > 100:
            max_page = 100

        return max_page

    @retry(stop=stop_after_attempt(3))
    def parse_taobao(self, url, detail_id, user_id, title, product_pic):
        headers = {
            'referer': url,
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/99.0.4844.84 Safari/537.36',
            'cookie': 'thw=my; enc=kEZ%2F6Bl2vFWfIFsHfhF9xIEtDjCxHH1tgot2FsrGQ%2B1vAqH1TtZp5BOx93Yb6DW3BHzYKb0sxPdNphFw9LbVblvvP08UkGEuWwztEPLcZO4%3D; _uab_collina=164812618539110271466536; _umdata=G5C213E4FCCC1C81F8366EC84DB37E4CEBD73B5; t=0f1c0fa6207ccc8c9aed88551f6cc40a; cna=jxZDGkDRZ1wCAXHTssf8HW1A; _m_h5_tk=afcd8b41b176b85e9bec900e9c42956c_1648621369472; _m_h5_tk_enc=3a20673ceb4060011111fb77c26b4da2; cookie2=154171c46e6adeb62f9b4e0408a581f7; _tb_token_=eb3138e65b68e; _samesite_flag_=true; sgcookie=E100RAwcoi65jaAzcO0%2Brkq5%2FlC%2BvCDQTkJ30jyqJs0VqMBnQuyjr36I%2FFCsVtIS7XcOHVNDeoQ6dL7Q2sdQj222AFQU42slsXCHH%2BeJl2lAEKfP51ige2MIwBJKGDf7DJfC; unb=2200802210051; uc3=vt3=F8dCvCtOrRSyfkLJvoQ%3D&nk2=F5RGNshDKWCjWwg%3D&lg2=URm48syIIVrSKA%3D%3D&id2=UUphyuFAMrJT7D%2F1zA%3D%3D; csg=d9b1e4b5; lgc=tb302737652; cancelledSubSites=empty; cookie17=UUphyuFAMrJT7D%2F1zA%3D%3D; dnk=tb302737652; skt=b6a79655ae05946f; existShop=MTY0ODYxMzQ4Mw%3D%3D; uc4=nk4=0%40FY4NA16CsQLCqWady9AJ0cvPxsKLrw%3D%3D&id4=0%40U2grEadIaFDbg5h%2FEAV4ILiqDDYkL0x7; tracknick=tb302737652; _cc_=VT5L2FSpdA%3D%3D; _l_g_=Ug%3D%3D; sg=213; _nk_=tb302737652; cookie1=UNDQTuyfHAAscizotGCJrDe8FsT10oNEjwnwyzIh2sA%3D; mt=ci=2_1; uc1=cookie16=UtASsssmPlP%2Ff1IHDsDaPRu%2BPw%3D%3D&pas=0&cookie14=UoewCLe9NCF4og%3D%3D&existShop=false&cookie15=UIHiLt3xD8xYTw%3D%3D&cookie21=WqG3DMC9FxUx; tfstk=cO21Bw04mFYsxpf2QlsFQBfCyeHNawKSc1ggfSlsm3RyXGZsJsqeU4_NqSYx3mnC.; l=eBj34VKrgCcTokGABO5BPurza77TzIRb8kPzaNbMiInca6_CZUaqqNC3ii12odtfgtCv-etrwOU8WRHWWE4d0ETNJqHzH13jnxvO.; isg=BOHh1jndJ_MNvYgFxNnwjGcd8K37jlWABp6aw0O2O-hjqgB8i9yPUBqsDF4see24'
        }

        params = {
            'auctionNumId': detail_id,
            'userNumId': user_id,
            'currentPageNum': '1',
            'pageSize': '20',
            'rateType': '',
            'orderType': 'sort_weight',
            'attribute': '',
            'sku': '',
            'hasSku': 'false',
            'folded': '0',
            'ua': '098#E1hvx9vUvbpvUvCkvvvvvjiWR2LO1jtjRLsOzjljPmP9tjlUnLdh1jnVR2LW1jECi9hvChCvCCpRvpvhvv2MMQvCvvXvovvvvvvUvpCWpQD5v8RJw6nQpd2XrqpyCjCbFO7t+eCowZSEDLuTWD19C7zheTtdpVQHYRp4ecEJnDeDyBvOJ193Zi7vVBDTmmxBlwyzhmyZEcqUaO9CvvXmp99h5EAIvpvUphvhMJAxoB0gvpvIphvvvvvvphCvpCQmvvCvehCvjvUvvhBGphvwv9vvBHBvpCQmvvChx29CvvBvpvvv',
            '_ksTS': str(time.time() * 1000).replace('.', '_'),
            'callback': 'jsonp_tbcrate_reviews_list'
        }

        try:
            response = requests.get(self.taobao_comments_url, params=params, headers=headers, timeout=10)

        except:
            print("请求超时，重连中！")

            time.sleep(self.sleep_time)
            raise Exception

        json_content = json.loads(re.search(r'jsonp_tbcrate_reviews_list\((.*?)\)', response.text).group(1))

        max_page = self.parse_taobao_comments(json_content, url, detail_id, user_id, title, product_pic, headers, params)
        if max_page > 1:
            time.sleep(self.sleep_time)

            for page in range(1, int(max_page + 1)):
#            for page in range(1, 2):
                self.parse_next_taobao_page(page, url, detail_id, user_id, title, product_pic)

                time.sleep(self.sleep_time)

        else:
            return True

    @retry(stop=stop_after_attempt(3))
    def parse_next_taobao_page(self, page, url, detail_id, user_id, title, product_pic):
        headers = {
            'referer': url,
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/99.0.4844.84 Safari/537.36',
            'cookie': 'thw=my; enc=kEZ%2F6Bl2vFWfIFsHfhF9xIEtDjCxHH1tgot2FsrGQ%2B1vAqH1TtZp5BOx93Yb6DW3BHzYKb0sxPdNphFw9LbVblvvP08UkGEuWwztEPLcZO4%3D; _uab_collina=164812618539110271466536; _umdata=G5C213E4FCCC1C81F8366EC84DB37E4CEBD73B5; t=0f1c0fa6207ccc8c9aed88551f6cc40a; cna=jxZDGkDRZ1wCAXHTssf8HW1A; _m_h5_tk=afcd8b41b176b85e9bec900e9c42956c_1648621369472; _m_h5_tk_enc=3a20673ceb4060011111fb77c26b4da2; cookie2=154171c46e6adeb62f9b4e0408a581f7; _tb_token_=eb3138e65b68e; _samesite_flag_=true; sgcookie=E100RAwcoi65jaAzcO0%2Brkq5%2FlC%2BvCDQTkJ30jyqJs0VqMBnQuyjr36I%2FFCsVtIS7XcOHVNDeoQ6dL7Q2sdQj222AFQU42slsXCHH%2BeJl2lAEKfP51ige2MIwBJKGDf7DJfC; unb=2200802210051; uc3=vt3=F8dCvCtOrRSyfkLJvoQ%3D&nk2=F5RGNshDKWCjWwg%3D&lg2=URm48syIIVrSKA%3D%3D&id2=UUphyuFAMrJT7D%2F1zA%3D%3D; csg=d9b1e4b5; lgc=tb302737652; cancelledSubSites=empty; cookie17=UUphyuFAMrJT7D%2F1zA%3D%3D; dnk=tb302737652; skt=b6a79655ae05946f; existShop=MTY0ODYxMzQ4Mw%3D%3D; uc4=nk4=0%40FY4NA16CsQLCqWady9AJ0cvPxsKLrw%3D%3D&id4=0%40U2grEadIaFDbg5h%2FEAV4ILiqDDYkL0x7; tracknick=tb302737652; _cc_=VT5L2FSpdA%3D%3D; _l_g_=Ug%3D%3D; sg=213; _nk_=tb302737652; cookie1=UNDQTuyfHAAscizotGCJrDe8FsT10oNEjwnwyzIh2sA%3D; mt=ci=2_1; uc1=cookie16=UtASsssmPlP%2Ff1IHDsDaPRu%2BPw%3D%3D&pas=0&cookie14=UoewCLe9NCF4og%3D%3D&existShop=false&cookie15=UIHiLt3xD8xYTw%3D%3D&cookie21=WqG3DMC9FxUx; tfstk=cO21Bw04mFYsxpf2QlsFQBfCyeHNawKSc1ggfSlsm3RyXGZsJsqeU4_NqSYx3mnC.; l=eBj34VKrgCcTokGABO5BPurza77TzIRb8kPzaNbMiInca6_CZUaqqNC3ii12odtfgtCv-etrwOU8WRHWWE4d0ETNJqHzH13jnxvO.; isg=BOHh1jndJ_MNvYgFxNnwjGcd8K37jlWABp6aw0O2O-hjqgB8i9yPUBqsDF4see24'
        }

        params = {
            'auctionNumId': detail_id,
            'userNumId': user_id,
            'currentPageNum': page,
            'pageSize': '20',
            'rateType': '',
            'orderType': 'sort_weight',
            'attribute': '',
            'sku': '',
            'hasSku': 'false',
            'folded': '0',
            'ua': '098#E1hvx9vUvbpvUvCkvvvvvjiWR2LO1jtjRLsOzjljPmP9tjlUnLdh1jnVR2LW1jECi9hvChCvCCpRvpvhvv2MMQvCvvXvovvvvvvUvpCWpQD5v8RJw6nQpd2XrqpyCjCbFO7t+eCowZSEDLuTWD19C7zheTtdpVQHYRp4ecEJnDeDyBvOJ193Zi7vVBDTmmxBlwyzhmyZEcqUaO9CvvXmp99h5EAIvpvUphvhMJAxoB0gvpvIphvvvvvvphCvpCQmvvCvehCvjvUvvhBGphvwv9vvBHBvpCQmvvChx29CvvBvpvvv',
            '_ksTS': str(time.time() * 1000).replace('.', '_'),
            'callback': 'jsonp_tbcrate_reviews_list'
        }

        try:
            response = requests.get(self.taobao_comments_url, params=params, headers=headers, timeout=10)

        except:
            print("请求超时，重连中！")
            time.sleep(self.sleep_time)
            raise Exception

        json_content = json.loads(re.search(r'jsonp_tbcrate_reviews_list\((.*?)\)', response.text).group(1))

        self.parse_taobao_comments(json_content, url, detail_id, user_id, title, product_pic ,headers,params)

    def parse_taobao_comments(self, json_content, url, detail_id, user_id, title, product_pic,headers,params):
        comments_list = json_content['comments']
        for comments in comments_list:
            username = comments["user"]['nick']
            comments_id = comments['rateId']
            content = comments['content']

            if len(comments['photos']) == 0:
                pic_result = "空"

            else:
                pic_result = []
                for pic in comments['photos']:
                    ###########
                    save_path_pic='D:/买家图片/'
                    if not os.path.exists(save_path_pic):
                        os.makedirs(save_path_pic)
                    ranstr=randint(0,10000)
                    ranstr=str(ranstr)
                    with open(save_path_pic.rstrip('/')+'/'+ranstr+pic['url'][-4:].replace('/',''),'wb') as f:
                        img_get=requests.get('https:'+pic['url'], params=params, headers=headers, timeout=10).content
                        f.write(img_get)
                    ###########
                    pic_result.append("https:" + pic['url'])

            comments_date = comments['date']

            result = [url, detail_id, user_id, title, product_pic, username, comments_id, content, pic_result, comments_date]
            self.save_to_csv(result)

        max_page = json_content['maxPage']
        if max_page > 100:
            max_page = 100

        return max_page

    def create_csv(self):
        file = open(self.save_path, 'w', encoding='utf-8-sig', errors='ignore', newline='')
        writer = csv.writer(file)

        writer.writerow(["链接", "商品ID", "用户ID", "商品标题", "商品图片", '用户评论', '评论ID', '评论内容', '评论照片', "评论时间"])

        file.close()

    def save_to_csv(self, result_item):
        file = open(self.save_path, 'a', encoding='utf-8-sig', errors='ignore', newline='')
        writer = csv.writer(file)

        writer.writerow(result_item)
        print(">>>", result_item)

        file.close()

    def main(self):
        dataframe = pandas.read_excel(self.read_path)

        url = dataframe['链接'].tolist()
        detail_id = dataframe['商品ID'].tolist()
        user_id = dataframe['用户ID'].tolist()
        title = dataframe['商品标题'].tolist()
        pic_url = dataframe["商品照片"].tolist()

        count = 1
        for url, detail_id, user_id, title, pic_url in zip(url, detail_id, user_id, title, pic_url):
            if count <= 1 and (count-1)<=len(url):
            # if count == 10:
                if 'tmall' in url:
                    self.parse_tmall(url, detail_id, user_id, title, pic_url)

                elif 'taobao' in url:
                    self.parse_taobao(url, detail_id, user_id, title, pic_url)

                else:
                    print("未知链接 >", url)
                    continue

                time.sleep(self.sleep_time)
                count += 1

            else:
#                count += 1
#                continue
                 break


if __name__ == '__main__':
    spider = Taobao_Comments()
    spider.main()
