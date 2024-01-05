#coding: utf-8
import re
import xlsxwriter
from io import BytesIO
from urllib.parse import urlencode
from sunday.core import Logger, getParser, Fetch, printTable, Auth, MultiThread
from sunday.tools.haodf.params import CMDINFO
from sunday.tools.haodf.utils import code2name_province
from bs4 import BeautifulSoup
from pydash import find

logger = Logger(CMDINFO['description']).getLogger()

class HaodfDoctor():
    def __init__(self, *args, **kwargs):
        urlBase = 'https://haodf.com'
        self.urls = {
                'list': urlBase + '/doctor/list-{province}-{typename}.html',
                'detail': urlBase + '/doctor/{doctor_id}.html',
                }
        self.headers = {
                'Content-Type': 'application/x-www-form-urlencoded'
                }
        self.fetch = Fetch()
        self.province = None
        self.typename = None
        self.thread_num = None
        self.doctors = []
        self.tableTitleList = [{
                'key': 'head',
                'title': '头像',
                }, {
                'key': 'name',
                'title': '姓名',
                }, {
                'key': 'level',
                'title': '职称',
                }, {
                'key': 'hospital',
                'title': '医院',
                }, {
                'key': 'typename',
                'title': '科室',
                }, {
                'key': 'province',
                'title': '省份',
                }, {
                'key': 'address',
                'title': '地址',
                }, {
                'key': 'schedule',
                'title': '门诊',
                }, {
                'key': 'introduction',
                'title': '简介',
                }]

    def initAuth(self):
        auth = Auth('not', '[好大夫在线]')
        self.province = auth.addParams('province', value=self.province, tip='省份', isSave=False)
        self.typename = auth.addParams('typename', value=self.typename, tip='科室名称', isSave=False)

    def getMaxNum(self):
        res = self.fetch.get(self.urls['list'].format(typename=self.typename, province=self.province))
        soup = BeautifulSoup(res.text, 'lxml')
        pageEle = soup.select('.page_turn_a')
        if len(pageEle) > 0:
            return int(re.findall(r'\d+', pageEle[-1].text)[0])
        lis = soup.select('.fam-doc-li')
        if len(lis) > 0:
            self.parseList(res.text)
        return 0

    def getAddress(self, url):
        if not url: return ''
        res = self.fetch.get(url)
        soup = BeautifulSoup(res.text, 'lxml')
        return self.getText(soup, '.hos-address')

    def getText(self, soup, pathstr):
        ele = soup.select_one(pathstr)
        try:
            return ele.text.strip()
        except Exception as e:
            return ''

    def parseDetail(self, doctor_id):
        res = self.fetch.get(self.urls['detail'].format(doctor_id=doctor_id))
        soup = BeautifulSoup(res.text, 'lxml')
        eles = [*soup.select('.doctor-faculty a'), *soup.select('.doctor-faculty span')]
        faculty = [(ele.text.strip(), ele.attrs.get('href')) for ele in eles]
        hospital, typename, *_ = faculty
        address = self.getAddress(hospital[1]).replace('地址：', '')
        head_url = soup.select_one('.profile-avatar img').attrs.get('src')
        schedule = [{
            'date': self.getText(ele, '.schedule-date'),
            'type': self.getText(ele, '.schedule-type'),
        } for ele in soup.select('.schedule-item')]
        self.doctors.append({
            'id': doctor_id,
            'head_url': head_url,
            'head_stream': self.fetch.get(head_url).content,
            'name': self.getText(soup, '.doctor-name'),
            'level': self.getText(soup, '.doctor-title'),
            'hospital': hospital[0],
            'typename': typename[0],
            'address': address,
            'schedule': schedule,
            'province': code2name_province(self.province),
            'introduction': self.getText(soup, '.doc-introduction'),
            })

    def parseList(self, text):
        soup = BeautifulSoup(text, 'lxml')
        lis = soup.select('.fam-doc-li')
        for li in lis:
            src = li.attrs.get('data-src')
            doctor_id = re.findall(r'\d+', src)[0]
            self.parseDetail(doctor_id)

    def parseListWrap(self, pages):
        for page in pages:
            res = self.fetch.get(self.urls['list'].format(typename=self.typename, province=self.province) + f'?p={page}')
            self.parseList(res.text)

    def saveExcel(self):
        workbook = xlsxwriter.Workbook('./output.xlsx')
        bold = workbook.add_format({'bold': True})
        cell_format = workbook.add_format()
        cell_format.set_text_wrap()
        cell_format.set_align('center')
        cell_format.set_align('vcenter')
        worksheet = workbook.add_worksheet()
        worksheet.set_default_row(80)
        worksheet.set_row(0, 30)
        worksheet.set_column('A:F', 15)
        worksheet.set_column('G:G', 50)
        worksheet.set_column('H:H', 35)
        worksheet.set_column('D:D', 25)
        worksheet.set_column('I:I', 80)
        for idx, item in enumerate(self.tableTitleList):
            worksheet.write(0, idx, item.get('title'), cell_format)
            for didx, doctor in enumerate(self.doctors):
                if item.get('key') == 'head':
                    worksheet.insert_image(didx + 1, idx, doctor['name'], { 'image_data': BytesIO(doctor.get('head_stream')), 'x_scale': 0.5, 'y_scale': 0.5 })
                if item.get('key') == 'schedule':
                    text = '\n'.join([f"{item.get('date')}: {item.get('type')}" for item in doctor.get(item.get('key'))])
                    worksheet.write(didx + 1, idx, text, cell_format)
                else:
                    worksheet.write(didx + 1, idx, doctor.get(item.get('key')), cell_format)
        workbook.close()

    def run(self):
        self.initAuth()
        maxNum = self.getMaxNum()
        if maxNum == 0: return
        pages = [num + 1 for num in range(maxNum)]
        if self.thread_num:
            multiData = [[item for item in pages[i::self.thread_num]] for i in range(self.thread_num)]
            MultiThread(multiData, lambda item, _: [self.parseListWrap, (item,)]).start()
        else:
            self.parseListWrap(pages)
        self.saveExcel()


def runcmd():
    parser = getParser(**CMDINFO)
    handle = parser.parse_args(namespace=HaodfDoctor())
    handle.run()


if __name__ == "__main__":
    runcmd()
