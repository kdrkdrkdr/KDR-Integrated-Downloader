#-*- coding:utf-8 -*-

from bs4 import BeautifulSoup
from requests import get, exceptions, Session, adapters
from reportlab.pdfgen.canvas import Canvas
from signal import signal, SIGINT, SIG_IGN
from ping3 import ping
from sys import exit as terminate
from shutil import rmtree
from os import mkdir, chdir, walk
from os.path import join
from zipfile import ZipFile
from PIL.Image import open as IMGOPEN
from re import sub
from click import clear as ClearWindow
from random import choice
from urllib.parse import urlparse
from threading import Thread
from queue import Queue


gAddress = 'https://e-hentai.org/g/'

class HostHeaderSSLAdapter(adapters.HTTPAdapter):
    
    def resolve(self, hostname):
        dnsList = [
            '1.1.1.1',
            '1.0.0.1',
        ]
        resolutions = {'e-hentai.org': choice(dnsList)}
        return resolutions.get(hostname)


    def send(self, request, **kwargs):
        connection_pool_kwargs = self.poolmanager.connection_pool_kw

        result = urlparse(request.url)
        resolvedIP = self.resolve(result.hostname)

        if result.scheme == 'https' and resolvedIP:
            request.url = request.url.replace(
                'https://' + result.hostname,
                'https://' + resolvedIP,
            )
            connection_pool_kwargs['server_hostname'] = result.hostname 
            connection_pool_kwargs['assert_hostname'] = result.hostname
            request.headers['Host'] = result.hostname

        else:
            connection_pool_kwargs.pop('server_hostname', None)
            connection_pool_kwargs.pop('assert_hostname', None)

        return super(HostHeaderSSLAdapter, self).send(request, **kwargs)


s = Session()

s.mount('https://', HostHeaderSSLAdapter())

header = {
    'User-agent' : 'Mozilla/5.0',
    'Referer' : gAddress
}

hParser = 'html.parser'


def CheckInternet():
    try:
        if ping('e-hentai.org') == None:
            terminate('인터넷 연결 또는 서버가 내려갔는지 확인하세요.')
    except ( OSError ):
        terminate('인터넷 연결 체크에 문제가 발생했습니다.')



def PrintInfo(info):
    print('\n[E-HentaiDownloader] {} \n'.format(info))



def PrintBanner():
    print('''
마지막 수정 날짜 : 2020/01/03
제작자 : kdr (https://github.com/kdrkdrkdr/)
  ______      _    _            _        _                  
 |  ____|    | |  | |          | |      (_)                 
 | |__ ______| |__| | ___ _ __ | |_ __ _ _   ___  _ __ __ _ 
 |  __|______|  __  |/ _ \ '_ \| __/ _` | | / _ \| '__/ _` |
 | |____     | |  | |  __/ | | | || (_| | || (_) | | | (_| |
 |______|    |_|  |_|\___|_| |_|\__\__,_|_(_)___/|_|  \__, |
                                                       __/ |
                                                      |___/ 
               동인지 다운로더 by kdr
    \n''')



def MakeZIP(directory, ZipName):
    JPGPath = []
    for root, directories, files in walk(directory):
        for filename in files:
            filepath = join(root, filename)
            JPGPath.append(filepath)
    
    with ZipFile(ZipName, 'w') as z:
        for jpg in JPGPath:
            z.write(jpg)

    
    rmtree(f'./{directory}/', ignore_errors=True)
    

def GetIMGsSize(imgPath):
    img = IMGOPEN(imgPath)
    return img.size



def MakePDF(ImageList, Filename, DirLoc):
    while True:
        try:
            c = Canvas(Filename)
            mask = [0, 0, 0, 0, 0, 0]

            if len(ImageList) == 1: 
                IMGsSize = GetIMGsSize(ImageList[0])
            else:
                IMGsSize = GetIMGsSize(ImageList[1])

            iWidth = IMGsSize[0]
            iHeight = IMGsSize[1]
            c.setPageSize((iWidth, iHeight))

            for i in range(len(ImageList)):
                pageNum = c.getPageNumber()
                c.drawImage(ImageList[i], x=0, y=0, width=iWidth, height=iHeight, mask=mask)
                c.showPage()
            c.save()
            rmtree(DirLoc, ignore_errors=True)
        
            break

        except OSError:
            continue




def GetSoup(queue, url):
    while True:
        try:
            html = s.get(url, headers=header).text
            soup = BeautifulSoup(html, hParser)
            break
        except (exceptions.ChunkedEncodingError, exceptions.SSLError, exceptions.Timeout, exceptions.ConnectionError):
            pass

    queue.put(soup)



def FastGetSoup(url):

    q = Queue()
    t = Thread(target=GetSoup, args=(q, url, ))
    t.start()

    soupObj = q.get()
    t.join()

    t._stop()

    return soupObj




def ImageDownload(filename, url):
    while True:
        try:
            with open(filename, 'wb') as f:
                resp = s.get(url, headers=header).content
                f.write(resp)
                break
        except ( exceptions.ChunkedEncodingError, exceptions.Timeout, exceptions.ConnectionError ):
            continue


def FastDownload(filename, url):
    t = Thread(target=ImageDownload, args=(filename, url,))
    t.setDaemon(False)
    t.start()
    t.join()
    t._stop()
            


def InitPool():
    signal(SIGINT, SIG_IGN)



def PrintProgressBar(iteration, total, prefix='', suffix='', decimals=1, length=50, fill='#'):
    percent = ("{0:." + str(decimals) + "f}").format(100 * (iteration / float(total)))
    filledLength = int(length * iteration // total)
    bar = fill * filledLength + ' ' * (length - filledLength)
    print(f'\r{prefix} |{bar}| {percent}% {suffix}', end='\r')
    if iteration == total: 
        print()



def Search():
    while True:
        try:
            sSelect = int(
                input(
                    '\n1. 페이지로 찾기'
                    '\n2. 검색어로 찾기'
                    '\n3. 뒤로 가기'
                    '\n\n검색할 방법을 선택하세요. : '
                )
            )
        

            if sSelect == 1:
                while True:
                    try:
                        page = int(input('검색할 페이지 번호를 입력하세요. (0을 입력하면 검색종료) : '))
                        if page <= 0:
                            ClearWindow(); break
                    
                        ClearWindow()
                        url = "https://e-hentai.org/?page={}".format(page-1)
                        soup = FastGetSoup(url)

                        Gallery = soup.find('table', {'class':'itg gltc'}).find_all('tr')

                        PrintInfo("{}페이지의 검색 결과입니다.".format(page))
                        print("="*30)

                        for g in Gallery:
                            try:
                                td = g.find_all('td')[2]
                                
                                title = td.find('div', {'class':'glink'}).text
                                link = td.find('a')['href']

                                print('\n제목 : {}'.format(title))
                                print('링크 : {}\n'.format(link))

                            except (IndexError, AttributeError, TypeError):
                                pass

                        print("\n" + "="*30 + "\n")

                    except ( ValueError, EOFError, KeyboardInterrupt, UnboundLocalError, NameError ):
                        ClearWindow()
                        PrintInfo('다시 입력해주세요.')


            elif sSelect == 2:
                while True:
                    try:
                        sWord = str(input("검색어를 입력하세요. (exit 입력하면 검색종료) : "))
                        if sWord.replace(' ', '') == 'exit':
                            ClearWindow(); break

                        sPage = int(input("몇쪽까지 검색할지 입력하세요. (0을 입력하면 검색종료) : "))
                        if sPage <= 0: 
                            ClearWindow(); break
                    
                        finish = False
                        ClearWindow()
                        for i in range(sPage):
                            url = "https://e-hentai.org/?page={}&f_search={}".format(i, sWord)
                            soup = FastGetSoup(url)

                            try:
                                tr = soup.find('table', {'class':'itg gltc'}).find_all('tr')
                            except AttributeError:
                                PrintInfo("검색 결과가 없습니다.")

                            
                            print("\n" + "="*30)

                            for t in tr:
                                if "No unfiltered results in this page range. You either requested an invalid page or used too aggressive filters." in t.text:
                                    PrintInfo("모두 검색했습니다.")
                                    finish = True
                                    break

                                td = t.find_all('td', {'class':'gl3c glname'})

                                for info in td:
                                    title = info.find('div', {'class':'glink'}).text
                                    link = info.find('a')['href']

                                    print('\n제목 : {}'.format(title))
                                    print('링크 : {}\n'.format(link))

                            if finish == True:
                                break

                            if finish == False:
                                print("="*30)
                                PrintInfo("{}페이지의 검색 결과입니다.".format(i+1))
                                
                    except ( ValueError, EOFError, KeyboardInterrupt, UnboundLocalError, NameError ):
                        ClearWindow()
                        PrintInfo('다시 입력해주세요.')


            elif sSelect == 3:
                ClearWindow(); break

            else:
                ClearWindow()
                PrintInfo('다시 입력해주세요.')

        except ( ValueError, EOFError, KeyboardInterrupt, NameError ):
            ClearWindow()
            PrintInfo('다시 입력해주세요.')

# pages = (pageCount // 40) + 1
# iURLlist = []

# for i in range(pages):
#     url = gLink + "/?p={}".format(i)
#     soup = FastGetSoup(url)
#     imageURL = soup.find('div', {'id':'gdt'}).find_all('a')

#     for imgURL in imageURL:
#         iURL = imgURL['href']
#         iSoup = FastGetSoup(iURL)
#         realIMG = iSoup.find('img', {'id':'img'})['src']

#         if not realIMG in iURLlist:
#             iURLlist.append(realIMG)

def AppendURLs(IMGsHtml_ONE_PAGE, iURLlist):
    for imgURL in IMGsHtml_ONE_PAGE:
        iURL = imgURL['href']
        iSoup = FastGetSoup(iURL)
        realIMG = iSoup.find('img', {'id':'img'})['src']

        if not realIMG in iURLlist:
            iURLlist.append(realIMG)

def Download():
    while True:
        while True:
            gLink = str(input("다운로드할 갤러리의 링크를 입력하세요. (exit 입력하면 다운로드 종료) : ")).replace(' ', '')

            if gLink == 'exit':
                ClearWindow()
                return

            elif not gAddress in gLink:
                ClearWindow()
                PrintInfo('잘못된 URL 입니다.')
                break

            else:
                gNumber = gLink.split('/')[4]

                fType = str(input("저장할 파일 형태를 입력하세요. (zip 또는 pdf 입력, 기본값은 zip) : ")).replace(' ', '')

                if fType != "pdf":
                    fType = "zip"


                if gLink == 'exit':
                    ClearWindow(); break

                
                if gAddress in gLink:
                    PrintInfo('이미지 주소를 불러오는중입니다.')

                    gallInfo = []
                    imgList = []
                    c = 0
                    Canceled = False

                    pSoup = FastGetSoup(gLink)
                    
                    try:
                        gTitle = pSoup.find('h1', {'id':'gn'}).text
                        gInfo = pSoup.find('div', {'id':'gd3'})
                        gAuthor = gInfo.find('div', {'id':'gdn'}).find('a').text
                        gType = gInfo.find('div', {'id':'gdc'}).text

                        gallInfo.append(gTitle)
                        gallInfo.append(gAuthor)
                        gallInfo.append(gType)

                        gPostInfo = gInfo.find('div', {'id':'gdd'}).find_all('tr')
                        for i in range(len(gPostInfo)):
                            gallInfo.append(gPostInfo[i].find_all('td')[1].text)

                    except AttributeError:
                        ClearWindow()
                        PrintInfo("다운로드가 중지되었습니다.")
                        break

                    gInfoString = "\n"
                    gInfoString += (
                        "제목 : " + gallInfo[0] + "\n\n"
                        "업로더 : " + gallInfo[1] + "\n\n"
                        "종류 : " + gallInfo[2] + "\n\n"
                        "날짜 : " + gallInfo[3] + "\n\n"
                        "파일 크기 : " + gallInfo[7] + "\n\n"
                        "페이지 수 : " + gallInfo[8] + "\n\n"
                    ) 



                    getPage = pSoup.find('table').find_all('td', {'class':'gdt2'})[5].text
                    pageCount = int(sub('[pages]', '', getPage))
                    dirName = gNumber
                    filename = sub('[\/:*?"<>|]', '_', gTitle)


                    try:
                        mkdir('{}'.format(dirName))

                    except FileExistsError:
                        rmtree('{}'.format(dirName), ignore_errors=True)
                        mkdir('{}'.format(dirName))
                    
                    finally:
                        try: chdir('{}'.format(dirName))
                        except PermissionError: pass


                    pages = (pageCount // 40) + 1
                    iURLlist = []

                    for i in range(pages):
                        url = gLink + "/?p={}".format(i)
                        soup = FastGetSoup(url)
                        imageURL = soup.find('div', {'id':'gdt'}).find_all('a')

                        threadList = []
                        t = Thread(target=AppendURLs, args=(imageURL, iURLlist,))
                        t.setDaemon(False)
                        t.start()
                        threadList.append(t)

                        for thr in threadList:
                            if thr.is_alive():
                                thr.join()
                        t._stop()
                        
                    ClearWindow()
                    print(gInfoString)
                    for i in iURLlist:
                        try:
                            jpgFile = '{}.jpg'.format(c+1)
                            jpgLoc = './{}/{}'.format(gNumber, jpgFile)

                            PrintProgressBar(c, len(iURLlist), prefix='[E-hentai Downloader]', suffix=f"({c}/{len(iURLlist)})")
                            FastDownload(jpgFile, i)
                            imgList.append(jpgLoc)

                            c += 1
                        except ( KeyboardInterrupt, EOFError ):
                            Canceled = True
                            break
                    
                    ClearWindow()
                    chdir('../')


                    if Canceled == False:
                        fileLocation = "./{}.{}".format(filename, fType)

                        if fType == 'zip':
                            MakeZIP(dirName, fileLocation)
                            PrintInfo("\"{}\" 에 저장되었습니다.".format(fileLocation))
                        
                        if fType == 'pdf':
                            MakePDF(imgList, fileLocation, dirName)
                            PrintInfo("\"{}\" 에 저장되었습니다.".format(fileLocation))
                        
                    else:
                        PrintInfo("다운로드가 중지되었습니다.")
                        rmtree('./{}/'.format(dirName), ignore_errors=True)



def main():
    ClearWindow()
    CheckInternet()
    while True:
        try:
            PrintBanner()
            select = int(
                input(
                    '\n1. 갤러리 찾기'
                    '\n2. 갤러리 다운로드'
                    '\n3. 뒤로 가기'
                    '\n\n>> '
                )
            )

            if select == 1:
                Search()
            elif select == 2:
                Download()
            elif select == 3:
                ClearWindow(); break
            else:
                PrintInfo('다시 선택해주세요.'); continue
                
        except ( ValueError, KeyboardInterrupt, EOFError, NameError ):
            PrintInfo('다시 선택해주세요.')