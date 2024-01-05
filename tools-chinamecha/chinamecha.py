#coding: utf-8
import re
import xlsxwriter
import json
import tqdm
import time
from random import random
from os import path
from io import BytesIO
from urllib.parse import urlencode
from sunday.core import Logger, getParser, Fetch, printTable, Auth, MultiThread, printTable, getException
from sunday.tools.chinamecha.params import CMDINFO
from bs4 import BeautifulSoup
from pydash import find, get, chunk, uniq_by

CkError = getException({
    10001: '类型错误请核查',
    10002: '无法获取数据页数与条数',
    10003: '目标网站异常请稍后重试',
    10004: '关键页面元素未找到'
    })

logger = Logger(CMDINFO['description']).getLogger()

class Chinamecha():
    def __init__(self, *args, **kwargs):
        urlBase = 'http://www.chinamecha.com'
        self.urlBase = urlBase
        self.urls = {
                'list': urlBase + '/company/',
                }
        self.fetch = Fetch()
        self.range = None
        self.typename = None
        self.getUrlByType = None
        self.isShowlist = False
        self.companys = []
        self.thread_num = None
        self.tableTitleList = [{
                'key': 'name',
                'title': '公司名称',
                }, {
                'key': 'contactor',
                'title': '联系人',
                }, {
                'key': 'phone',
                'title': '手机',
                }, {
                'key': 'mobile',
                'title': '电话',
                }, {
                'key': 'fax',
                'title': '传真',
                }, {
                'key': 'good',
                'title': '货品描述',
                }, {
                'key': 'introduce',
                'title': '公司描述',
                }, {
                'key': 'url',
                'title': '数据来源',
                }]

    def printList(self):
        printTable(['编号', '类型', '代码', '链接'])(self.getAllTypes())

    def getAllTypes(self):
        res = self.fetch.get(self.urls['list'])
        soup = BeautifulSoup(res.text, 'lxml')
        links = soup.select('.jd_con_ul dl dd a')
        datas = [[
            idx + 1,
            it.text,
            it.attrs.get('href').split('/').pop().replace('.html', ''),
            self.urlBase + it.attrs.get('href'),
            ] for idx, it in enumerate(links)]
        def getUrlByType(typename):
            if typename == 'ALL': return [(it[2], it[3]) for it in datas]
            for it in datas:
                if it[1] == typename:
                    return it[2], it[3]
            raise CkError(10001, other=typename)
        self.getUrlByType = getUrlByType
        return datas

    def getPageInfo(self, url, fetch):
        res = fetch.get(url, timeout_time=10, timeout=60)
        soup = BeautifulSoup(res.text, 'lxml')
        pageEle = soup.select_one('#lblpage')
        if pageEle is None:
            logger.error(f'当前分类无数据{url}')
            raise CkError(10002)
        pageMat = re.match(r'.*共有(\d+?)条记录.*共(\d+?)页.*', pageEle.text.replace('\xa0', ''))
        if pageMat:
            return pageMat.groups()
        raise CkError(10002)

    def getPageCompany(self, urls, idx, update):
        fetch = Fetch()
        time.sleep(random())
        for url in urls:
            try:
                res = fetch.get(url, timeout_time=10, timeout=60)
                soup = BeautifulSoup(res.text, 'lxml')
                lis = soup.select('.jd_con_ul.jdqy li')
                for idx, li in enumerate(lis):
                    nameEle = li.select_one('.gy_list_info_title a')
                    goodEle = li.select_one('.gy_list_info_zy.jdqyzy')
                    if nameEle is None:
                        logger.error(f'列表页{url}第{idx + 1}项公司名不存在')
                        update()
                        continue
                    self.companys.append({
                        'name': nameEle.text.strip(),
                        'good': goodEle.text.strip() if goodEle else '',
                        'url': self.urlBase + nameEle.attrs.get('href'),
                        'code': nameEle.attrs.get('href').split('/').pop().replace('.html', ''),
                        })
            except Exception as e:
                logger.error(f'页面解析失败: {url}')
                logger.exception(e)
            time.sleep(random() * 2)
            update()

    def wrapper(self, func, items, *args):
        for item in items: func(item, *args)

    def getData(self, companys=None, deep=0):
        companys = companys or self.companys
        print(f'请求公司数据{len(self.companys)}条')
        if self.thread_num:
            MultiThread(companys, lambda *args: [self.getDataByCompany, args], self.thread_num).start(isBar=True)
        else:
            self.getDataByCompany(companys)
        if deep == 0:
            secondCompanys = [company for company in self.companys if company.get('success') == False]
            if len(secondCompanys) > 10:
                print('补充请求未有数据项')
                self.getData(secondCompanys, deep + 1)

    def getDataByCompany(self, companys, idx=None, update=None):
        fetch = Fetch(proxy='http://127.0.0.1:5555/random')
        time.sleep(random())
        for company in companys:
            try:
                res = fetch.get(company.get('url'), timeout_time=10, timeout=60)
                if not res.ok:
                    time.sleep(10)
                    update and update()
                    continue
                soup = BeautifulSoup(res.text, 'lxml')
                introduceEle = soup.select_one('.gsjj') or {}
                infoEle = soup.select_one('.gsmes')
                contactEle = infoEle.select('.mes-top')[1].select('.mes-list span')
                if contactEle is None: raise CkError(10004)
                company.update({
                    'contactor': get(contactEle, '0.text', '').strip(),
                    'mobile': get(contactEle, '1.text', '').strip(),
                    'phone': get(contactEle, '2.text', '').strip(),
                    'fax': get(contactEle, '3.text', '').strip(),
                    'introduce': get(introduceEle, 'text', '').strip(),
                    'success': True,
                    })
            except Exception as e:
                logger.exception(e)
                logger.error(f'获取数据失败：{company} => {company.get("url")}')
                company.update({
                    'success': False
                    })
            time.sleep(random() * 2)
            update and update()


    def getDataByPage(self, typenames=None):
        if path.exists('./companys.json'):
            with open('./companys.json', 'r') as f:
                self.companys = json.loads(f.read())
                logger.warning(f'存在公司列表，待采集公司数据 {len(self.companys)} 条')
            typerange = self.range.split('-')
            if len(typerange) == 2 and typerange[1]:
                start = int(typerange[0]) - 1
                end = int(typerange[1]) - 1
                self.companys = self.companys[start:end]
            else:
                start = int(typerange[0]) - 1
                self.companys = self.companys[start:]
            self.getData()
            return
        self.getAllTypes()
        if typenames is None: typenames = self.getUrlByType('ALL')
        urls = set()
        def genUrl(typenames, idx, update):
            fetch = Fetch()
            time.sleep(random())
            for typename in typenames:
                try:
                    code, url = self.getUrlByType(typename) if type(typename) == str else typename
                    (count, pages) = self.getPageInfo(url, fetch)
                    for idx in range(int(pages)):
                        page = str(idx + 1)
                        flag = f'yp_vlist_{code}_{page}' if typename else 'index'
                        urls.add(f'{self.urlBase}/company/{flag}.html')
                except Exception as e:
                    logger.error(f'页数据获取失败：{url}')
                    logger.exception(e)
                time.sleep(random() * 2)
                update()
        MultiThread(typenames, lambda *args: [genUrl, args], self.thread_num).start(isBar=True)
        urls = list(urls)
        if len(urls) == 0: raise CkError(10003)
        print(f'共有种类{len(typenames)}种，数据{len(urls)}页')
        MultiThread(urls, lambda *args: [self.getPageCompany, args], self.thread_num).start(isBar=True)
        self.companys = uniq_by(self.companys, lambda item: item.get('code'))
        with open('./companys.json', 'w+') as f: f.write(json.dumps(self.companys))
        self.getData()

    def saveExcel(self, filename='机电一体化网'):
        companys = [it for it in self.companys if it.get('success') == True]
        filepath = path.abspath(f'./{filename}{self.range or ""}.xlsx')
        print(f'全部数据{len(self.companys)}条，成功抓取{len(companys)}条, 保存文件：{filepath}')
        workbook = xlsxwriter.Workbook(filepath)
        bold = workbook.add_format({'bold': True})
        cell_format = workbook.add_format()
        cell_format.set_text_wrap()
        cell_format.set_align('center')
        cell_format.set_align('vcenter')
        worksheet = workbook.add_worksheet()
        worksheet.set_default_row(80)
        worksheet.set_row(0, 30)
        worksheet.set_column('A:A', 35)
        worksheet.set_column('B:E', 15)
        worksheet.set_column('F:F', 35)
        worksheet.set_column('G:G', 50)
        worksheet.set_column('H:H', 35)
        for idx, item in enumerate(self.tableTitleList):
            worksheet.write(0, idx, item.get('title'), cell_format)
            for didx, data in enumerate(companys):
                worksheet.write(didx + 1, idx, data.get(item.get('key')), cell_format)
        workbook.close()

    def run(self):
        if self.isShowlist:
            self.getAllTypes()
            self.printList()
        elif self.typename:
            self.getDataByPage(self.typename)
            self.saveExcel('-'.join(self.typename))
        else:
            self.getDataByPage()
            self.saveExcel()


def runcmd():
    parser = getParser(**CMDINFO)
    handle = parser.parse_args(namespace=Chinamecha())
    handle.run()


if __name__ == "__main__":
    runcmd()
