import os
import sys
import requests
from lxml import etree
import re
from fake_useragent import UserAgent
proxy   = {"http": "socks5://127.0.0.1:1082","https": "socks5://127.0.0.1:1082"}

# headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.93 Safari/537.36',
#            'accept-language': 'zh-TW;q=0.9,en;q=0.8,ja;q=0.7,zh-CN,zh;q=0.6', }
headers = {'User-Agent': UserAgent(verify_ssl=False).random,
           'accept-language': 'zh-TW;q=0.9,en;q=0.8,ja;q=0.7,zh-CN,zh;q=0.6', }

main_url= 'https://www.pixiv.net/'

def get_rank_url(session=None,mode='daily',page_num=1,page_sz=50):
    '''
    Dump ranking pages' artwork urls

    '''
    rank_url= 'https://www.pixiv.net/ranking.php'
    params = (  ('mode'   ,  mode ),
                ('content',  'illust') )    
    html_text = session.get(url=rank_url, headers=headers, params=params,proxies=proxy).text
    tree = etree.HTML(html_text)
    art_urls = tree.xpath('//section[@class="ranking-item"]/div[2]/a/@href')
    art_urls = [x[1:] for x in art_urls]
    if page_num>1:
        for p in range(2,page_num+1):
            params = (  ('mode', mode),
                        ('content', 'illust'),
                        ('p', str(p)),
                        ('format', 'json'))
            json_text = session.get(url=rank_url, headers=headers, params=params,proxies=proxy).json()
            others_list = json_text['contents']
            for i in range(page_sz):
                others_list[i] = 'artworks/' + str(others_list[i]['illust_id'])
            art_urls.extend(others_list)
    art_urls = [main_url+x for x in art_urls]
    return art_urls

def get_image_raw(session=None,art_url=None):
    '''
    Download the first piece of image from artworks url
    Such as https://www.pixiv.net/artworks/xxxxxxx

    '''
    headers.update({'accept': 'image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8'})
    headers.update({'sec-fetch-site': 'cross-site'}) # important!!!
    headers.update({'sec-fetch-mode': 'navigate'})
    headers.update({'sec-fetch-user': '?1'})
    headers.update({'sec-fetch-dest': 'document'})
    headers.update({'referer': main_url})
    html_text = session.get(url=art_url, headers=headers,proxies=proxy).text
    imag_url  = re.findall(r'"original":"(.*?)"',html_text)[0]
    imag_name = imag_url.split('/')[-1]
    response  = session.get(url=imag_url,headers=headers,proxies=proxy)
    if response.status_code !=200:
        print('Original imag requests with error response '+response.status_code)
        sys.exit(1)
    return imag_name,response.content
    
def dump_rank_img(session=None,mode='daily',page_num=1,page_sz=50):
    '''
    Dump ranking images
    mode='daily'|'weekly'|'monthly'
    page_sz=50 do not modify

    '''
    saved_dir=mode
    if not os.path.exists(saved_dir):
        os.mkdir(saved_dir)

    art_urls = get_rank_url(session,mode,page_num,page_sz)

    rank=1
    for art_url in art_urls:
        print('Get '+art_url,end='')
        imag_name,raw_bin = get_image_raw(session,art_url)
        path = saved_dir+'/'+str(rank)+'_'+imag_name
        with open(path,'wb') as f:
            f.write(raw_bin)
            print('=> '+path)
        rank+=1
    


if __name__ == '__main__':
    session = requests.session()
    # dump_rank_img(session,'daily',1,50)
    # dump_rank_img(session,'weekly',1,50)
    dump_rank_img(session,'monthly',2,50)

