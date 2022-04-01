import re
import csv
import json
import requests
import os
from tenacity import retry, stop_after_attempt


class TaoBao_Search:
    def __init__(self):
        self.save_path = 'taobao_search.csv'

        self.search_url = 'https://s.taobao.com/search?q=%E8%A5%BF%E6%9C%8D&type=p&tmhkh5=&from=sea_1_searchbutton&catId=100&spm=a2141.241046-.searchbar.d_2_searchbox'

        self.headers = {
            'referer': 'https://world.taobao.com/',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/99.0.4844.82 Safari/537.36',
            'cookie': 'thw=my; enc=kEZ%2F6Bl2vFWfIFsHfhF9xIEtDjCxHH1tgot2FsrGQ%2B1vAqH1TtZp5BOx93Yb6DW3BHzYKb0sxPdNphFw9LbVblvvP08UkGEuWwztEPLcZO4%3D; t=0f1c0fa6207ccc8c9aed88551f6cc40a; cna=jxZDGkDRZ1wCAXHTssf8HW1A; _m_h5_tk=afcd8b41b176b85e9bec900e9c42956c_1648621369472; _m_h5_tk_enc=3a20673ceb4060011111fb77c26b4da2; cookie2=154171c46e6adeb62f9b4e0408a581f7; _tb_token_=eb3138e65b68e; _samesite_flag_=true; sgcookie=E100RAwcoi65jaAzcO0%2Brkq5%2FlC%2BvCDQTkJ30jyqJs0VqMBnQuyjr36I%2FFCsVtIS7XcOHVNDeoQ6dL7Q2sdQj222AFQU42slsXCHH%2BeJl2lAEKfP51ige2MIwBJKGDf7DJfC; unb=2200802210051; uc1=cookie14=UoewCLe9Mgc18A%3D%3D&existShop=false&cookie15=Vq8l%2BKCLz3%2F65A%3D%3D&cookie21=VT5L2FSpczFp&cookie16=W5iHLLyFPlMGbLDwA%2BdvAGZqLg%3D%3D&pas=0; uc3=vt3=F8dCvCtOrRSyfkLJvoQ%3D&nk2=F5RGNshDKWCjWwg%3D&lg2=URm48syIIVrSKA%3D%3D&id2=UUphyuFAMrJT7D%2F1zA%3D%3D; csg=d9b1e4b5; lgc=tb302737652; cancelledSubSites=empty; cookie17=UUphyuFAMrJT7D%2F1zA%3D%3D; dnk=tb302737652; skt=b6a79655ae05946f; existShop=MTY0ODYxMzQ4Mw%3D%3D; uc4=nk4=0%40FY4NA16CsQLCqWady9AJ0cvPxsKLrw%3D%3D&id4=0%40U2grEadIaFDbg5h%2FEAV4ILiqDDYkL0x7; tracknick=tb302737652; _cc_=VT5L2FSpdA%3D%3D; _l_g_=Ug%3D%3D; sg=213; _nk_=tb302737652; cookie1=UNDQTuyfHAAscizotGCJrDe8FsT10oNEjwnwyzIh2sA%3D; JSESSIONID=B179F64932654DC88A99769D153441B8; alitrackid=world.taobao.com; lastalitrackid=world.taobao.com; tfstk=cfaNBnVY5NQZ-a3f2VgVCBCQ4T0OZ_VgielSjlBqIPO2afnGifvxtAGtTjOencf..; l=eBj34VKrgCcToCGBBOfCnurza779jIRYYuPzaNbMiOCPOafp5kn1W6VcIFL9Cn1Vh67JR3lRBzU9BeYBqIv4n5U62j-la_Mmn; isg=BNHRDXXLV6OHF7g1VKmA3PdN4N1rPkWwli6Kk7NmyBi3WvGs-4rBgA-4-K68yd3o'
        }

    @retry(stop=stop_after_attempt(3))
    def parse_search_result(self):
        try:
            response = requests.get(self.search_url, headers=self.headers, timeout=10)

        except:
            print("请求超时，重连中！")
            raise Exception

        json_content = json.loads(re.search('g_page_config = (.*?)}};', response.text).group(1) + "}}")

        count = 1

        # [3:] = 去掉无用的数据
        item_list = json_content['mods']["itemlist"]["data"]["auctions"][3:]
        for item in item_list:
            if count == 6:#####个数
                break

            detail_url = 'https:' + item['detail_url']
            detail_id = item['nid']
            user_id = item['user_id']
            title = item['raw_title']
            pic_url = 'https:' + item['pic_url']

            result = [detail_url, detail_id, user_id, title, pic_url]
            save_path_pic='D:/图片/'
            with open(save_path_pic.rstrip('/')+'/'+detail_id+pic_url[-4:],'wb') as f:
                img_get=requests.get(pic_url,headers=self.headers).content
                f.write(img_get)
            self.save_to_csv(result)
            
            count += 1

    def create_csv(self):
        file = open(self.save_path, 'w', encoding='utf-8-sig', errors='ignore', newline='')
        writer = csv.writer(file)

        writer.writerow(["链接", "商品ID", "用户ID", "商品标题", "商品照片"])

        file.close()

    def save_to_csv(self, result_item):
        file = open(self.save_path, 'a', encoding='utf-8-sig', errors='ignore', newline='')
        writer = csv.writer(file)

        writer.writerow(result_item)
        print(">>>", result_item)

        file.close()

    def main(self):
        self.create_csv()

        self.parse_search_result()


if __name__ == '__main__':
    spider = TaoBao_Search()
    spider.main()
#下载图片的