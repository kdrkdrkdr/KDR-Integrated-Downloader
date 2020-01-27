#-*-coding:utf-8 -*-

from bs4 import BeautifulSoup
from requests import get, exceptions, Session, adapters
from reportlab.pdfgen.canvas import Canvas
from signal import signal, SIGINT, SIG_IGN
from ping3 import ping
from sys import exit as terminate
from shutil import rmtree
from os import mkdir, chdir 
from PIL.Image import open as IMGOPEN
from re import sub
from click import clear as ClearWindow
from random import choice
from urllib.parse import urlparse
from keyboard import read_key
from threading import Thread
from queue import Queue


baseURL = "https://hiyobi.me"

class HostHeaderSSLAdapter(adapters.HTTPAdapter):
    
    def resolve(self, hostname):
        dnsList = [
            '1.1.1.1',
            '1.0.0.1',
        ]
        resolutions = {'hiyobi.me': choice(dnsList)}
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

hParser = 'html.parser'

infoBanner = "[Hiyobi-Downloader]"

header = {
    'User-agent' : 'Mozilla/5.0',
    'Referer' : baseURL,
}


PrintInfo = lambda info: print(f"\n{infoBanner} {info}\n")


def InitPool():
    signal(SIGINT, SIG_IGN)


def CheckInternet():
    try:
        if ping('8.8.8.8') == None:
            terminate('인터넷 연결 또는 서버가 내려갔는지 확인하세요.')
    except ( OSError ):
        terminate('리눅스 사용자는 root권한을 이용해주세요.')


def PrintBanner():
    print(
'''
마지막 수정 날짜 : 2020/01/17
제작자 : kdr (https://github.com/kdrkdrkdr/)
.-. .-..-..-.  .-..----. .----. .-.
| {_} || | \ \/ //  {}  \| {}  }| |
| { } || |  }  { \      /| {}  }| |
`-' `-'`-'  `--'  `----' `----' `-'
      Hiyobi Downloader by kdr
''')



def PrintProgressBar(iteration, total, prefix='', suffix='', decimals=1, length=50, fill='#'):
    percent = ("{0:." + str(decimals) + "f}").format(100 * (iteration / float(total)))
    filledLength = int(length * iteration // total)
    bar = fill * filledLength + ' ' * (length - filledLength)
    print(f'\r{prefix} |{bar}| {percent}% {suffix}', end='\r')
    if iteration == total: 
        print()


def GetFileName(filename):
    toReplace = {
        '\\':'', '/':'', ':':'-', '\"':'',
        '?':'', '<':'[', '>':']', '|':'-', '*':''
    }

    for key, value in toReplace.items():
        filename = str(filename).replace(key, value)

    return filename


def GetIMGsSize(imgPath):
    while True:
        try:
            img = IMGOPEN(imgPath)
            return img.size
        except:
            continue



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
            with open(f"{filename}", 'wb') as f:
                resp = s.get(url, headers=header, ).content
                f.write(resp)
                break

        except ( exceptions.ChunkedEncodingError, 
                 exceptions.Timeout,
                 exceptions.ConnectionError ):
            continue


def FastDownload(filename, url):
    t = Thread(target=ImageDownload, args=(filename, url,))
    t.setDaemon(False)
    t.start()
    t.join()
    t._stop()

    


def MakeDirectory(DirPath):
    try:
        mkdir(DirPath)
    except FileExistsError:
        rmtree(DirPath, ignore_errors=True)
        mkdir(DirPath)
    finally:
        chdir(DirPath)
        return True



def GetIMGsURL(gNum):
    jsonURL = baseURL + f'/data/json/{gNum}_list.json'
    imgURL = baseURL + f'/data/{gNum}/'
    
    while True:
        try: reqObj = s.get(jsonURL, headers=header, ).json(); break
        except: pass

    ListOfIMGsURL = [imgURL + i['name'] for i in reqObj]
    return ListOfIMGsURL



def GetGalleryInfo(gNum):
    infoURL = baseURL + f"/info/{gNum}"
    soup = FastGetSoup(infoURL)

    infoString = "\n"
    infoContainer = soup.find('div', {'class':'gallery-content row'})
    galleryInfos = infoContainer.find_all('tr')
    
    title = infoContainer.find('h5').text
    
    infoString += "제목 : " + title + "\n\n"

    for gInfo in galleryInfos:
        info = gInfo.find_all('td')
        infoString += info[0].text + info[1].text + '\n\n'

    return [title, infoString]



def hSearch():
    while True:
        try:
            kWord = str(input("\n검색할 동인지 이름을 입력하세요. (exit 입력하면 검색종료) : ")).replace(' ', '')
            if kWord.lower() == 'exit': ClearWindow(); break

            page = 1
            morePage = True
            while True:
                ClearWindow()
                soup = FastGetSoup(f"https://hiyobi.me/search/{kWord}/{page}")
                mainContainer = soup.find('main', {'class':'container'}).find_all('h5')

                if mainContainer == []:
                    PrintInfo("검색 결과가 없습니다.")
                    break

                else:
                    PrintInfo(f"{page}페이지 검색 결과입니다.")
                    for j in mainContainer:
                        dTitle = j.a.text
                        dLink = j.a['href']
                        print('-'*80)
                        print("제목 : ", dTitle)
                        print("링크 : ", dLink)
                print('-'*80, '\n')


                PrintInfo("이전페이지: 아래 방향키, 다음 페이지: 위 방향키, 검색종료: Esc키")
                while True:
                    try:
                        rk = read_key()

                        if rk == 'down':
                            if page-1 != 0:
                                page -= 1
                            else:
                                PrintInfo("첫 페이지 입니다.")
                                continue

                        if rk == 'up':
                            page += 1

                        if rk == 'esc':
                            morePage = False

                        if rk in ['down', 'up', 'esc']:
                            break

                    except ( KeyboardInterrupt, EOFError ):
                        pass

                if morePage == False:
                    ClearWindow()
                    break


        except ( TypeError, KeyboardInterrupt, EOFError, UnboundLocalError):
            ClearWindow()
            PrintInfo("다시 입력해주세요.")


def hDownload():
    while True:
        try:
            mLink = str(input("다운로드할 동인지의 링크를 입력하세요. (exit 입력하면 다운로드 종료) : ")).replace(' ', '')
            if mLink == 'exit':
                ClearWindow()
                return

            elif not baseURL+'/reader/' in mLink:
                ClearWindow()
                PrintInfo("잘못된 URL입니다."); 
                continue

            else:
                ClearWindow()
                gNumber = sub('[^0-9]', '', mLink)

                Canceled = False
                imgLoc = []
                dirLoc = f'./{gNumber}/'
                
                imgURLs = GetIMGsURL(gNum=gNumber)
                info = GetGalleryInfo(gNum=gNumber)
                print(info[1])

                MakeDirectory(dirLoc)
                for imgs in enumerate(imgURLs):
                    try:
                        PrintProgressBar(imgs[0], len(imgURLs), prefix=f'{infoBanner}', suffix=f'({imgs[0]}/{len(imgURLs)})')
                        fname = f"{gNumber}_{imgs[0]+1}.jpg"
                        imgName = f"{dirLoc}{fname}"
                        FastDownload(fname, imgs[1])
                        imgLoc.append(imgName)

                    except ( KeyboardInterrupt, EOFError ):
                        Canceled = True
                        break
                
                ClearWindow()
                chdir('../')

                if Canceled == False:
                    pdfName = GetFileName(info[0]) + '.pdf'
                    MakePDF(imgLoc, pdfName, dirLoc)
                    PrintInfo(f"\"./{pdfName}\" 에 저장되었습니다.\n")

                else:
                    rmtree(dirLoc, ignore_errors=True)
                    PrintInfo('다운로드가 취소되었습니다.')
                    break


        except ( KeyboardInterrupt, EOFError ):
            PrintInfo("다시 입력해주세요.")


def main():
    CheckInternet()
    ClearWindow()
    while True:
        try:
            PrintBanner()
            select = int(
                input(
                    '\n1. 동인지 찾기'
                    '\n2. 동인지 다운로드'
                    '\n3. 뒤로 가기'
                    '\n\n>> '
                )
            )

            if select == 1:
                hSearch()
            elif select == 2:
                hDownload()
            elif select == 3:
                ClearWindow() 
                break
            else:
                ClearWindow()
                PrintInfo('다시 선택해주세요.')

                
        except ( ValueError, KeyboardInterrupt, EOFError, NameError ):
            ClearWindow()
            PrintInfo('다시 선택해주세요.')
