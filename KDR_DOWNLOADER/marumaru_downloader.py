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
from json import loads
from cfscrape import CloudflareScraper
from threading import Thread
from queue import Queue


baseURL = "https://marumaru.town"


class HostHeaderSSLAdapter(adapters.HTTPAdapter):
    
    def resolve(self, hostname):
        dnsList = [
            '1.1.1.1',
            '1.0.0.1',
        ]
        resolutions = {'marumaru.soy': choice(dnsList)}
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


cfs = CloudflareScraper()

cfs.mount('https://', HostHeaderSSLAdapter())

hParser = 'html.parser'

infoBanner = "[Marumaru-Downloader]"

header = {
    'User-agent' : 'Mozilla/5.0',
    'Referer' : baseURL,
}



def PrintBanner():
    print('''
마지막 수정 날짜 : 2020/01/17
제작자 : kdr (https://github.com/kdrkdrkdr/)
 _ __ ___   __ _ _ __ _   _ _ __ ___   __ _ _ __ _   _ 
| '_ ` _ \ / _` | '__| | | | '_ ` _ \ / _` | '__| | | |
| | | | | | (_| | |  | |_| | | | | | | (_| | |  | |_| |
|_| |_| |_|\__,_|_|   \__,_|_| |_| |_|\__,_|_|   \__,_|                                                       
                marumaru downloader
 ''')

PrintInfo = lambda info: print(f"\n{infoBanner} {info}\n")


def InitPool():
    signal(SIGINT, SIG_IGN)



def CheckInternet():
    try:
        if ping('8.8.8.8') == None:
            terminate('인터넷 연결 또는 서버가 내려갔는지 확인하세요.')
    except ( OSError ):
        terminate('리눅스 사용자는 root권한을 이용해주세요.')



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
            html = cfs.get(url, headers=header).text
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
                resp = cfs.get(url, headers=header, ).content
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



def GetImageURLs(mangaAddr):
    imgURLs = []
    soup = FastGetSoup(mangaAddr).find('div', {'class':'view-img'}).find_all('img')
    for i in soup:
        url = i['src']
        
        if not 'marumaru' in url:
            url = baseURL + url
        imgURLs.append(url)

    return imgURLs


def mSearch():
    while True:
        try:
            keyWord = str(input("검색어를 입력하세요. (exit을 입력하면 검색종료): ")).replace(' ', '')
            if keyWord.lower() == 'exit': break

            searchURL = f"{baseURL}/bbs/search.php?url=%2Fbbs%2Fsearch.php&stx={keyWord}"
            lstContainer = FastGetSoup(searchURL).find('div', {'class':'search-media'}).find_all('div', {'class':'media-heading'})

            if lstContainer == []:
                print("검색결과가 없습니다.")
            else:
                print("\n")
                for lstC in lstContainer:
                    mTitle = lstC.a.text.strip()
                    mLink = lstC.a['href']
                    print('-'*80)
                    print("제목 : ", mTitle)
                    print("링크 : ", baseURL + "/bbs/" + mLink)
                print('-'*80, '\n')
                

        except ( ValueError, EOFError, KeyboardInterrupt, NameError, UnboundLocalError ):
            ClearWindow()
            PrintInfo("다시 입력해주세요.")



def mDownload():
    while True:
        try:
            maruLink = str(input('다운로드 할 마나모아 만화 링크를 입력하세요. (exit을 입력하면 다운로드 종료): '))
            if maruLink.replace(' ', '') == 'exit': break

            PrintInfo("횟차를 불러오는 중입니다...")

            soup = FastGetSoup(maruLink)
            chapterList = list(soup.find_all('td', {'class':'list-subject'}))
            chapterList.reverse()

            bigTitle = soup.title.text.replace('MARUMARU - 마루마루 - ', '')

            epiList = []
            for ch in chapterList:
                epiTitle = sub('[\t]', '', ch.a.text.strip())
                epiLink = ch.a['href']
                if not 'marumaru' in epiLink:
                    epiLink = baseURL + epiLink
                epiList.append([epiTitle, epiLink])

            print()
            for epi in enumerate(epiList):
                print("-"*80, f"\n{epi[0]+1}. {epi[1][0]}")
            print("-"*80, '\n')


            sIndex = str(input("""
다운로드 받고 싶은 횟차를 입력하세요. (exit 입력하면 다운로드 종료)
(사용법) 1화 ~ 10화, 12화 모두 다운로드 : 1~10, 12 
: """)).replace(' ', '').split(',')
            if sIndex == 'exit': break

            episode = []
            for e in sIndex:
                if '~' in e:
                    s = e.split('~')

                    s1 = int(s[0])
                    s2 = int(s[1])

                    if s1 <= s2: 
                        InDe = 1
                    else:
                        InDe = -1

                    section = list(range(int(s[0]), int(s[1])+InDe, InDe))

                else:
                    section = [int(e)]

                for sec in section:
                    if sec <= 0:
                        section.remove(sec)

                episode.extend(section)
            
            FinalInfo = ""
            Canceled = False

            for epi in episode:
                try:
                    mTitle = epiList[epi-1][0]
                    mLink = epiList[epi-1][1]
                except ( IndexError ):
                    PrintInfo(f"{epi}화는 잘못된 횟차 수 입니다.")
                    break


                mangaIMGURL = GetImageURLs(mangaAddr=mLink)
                filename = GetFileName(mTitle)

                dirLoc = f"./marumaru_temp/"
                imgLoc = []
                ClearWindow()

                print(f'\n제목 : {bigTitle}'
                    + f'\n\n횟차 : {epi}화\n')

                MakeDirectory(dirLoc)
                for imgs in enumerate(mangaIMGURL):
                    try:
                        PrintProgressBar(imgs[0], len(mangaIMGURL), prefix=f'{infoBanner}', suffix=f'({imgs[0]}/{len(mangaIMGURL)})')
                        jpgName = f"{imgs[0]+1}.jpg"
                        imgName = f"{dirLoc}{jpgName}"
                        FastDownload(jpgName, imgs[1])
                        imgLoc.append(imgName)

                    except ( KeyboardInterrupt, EOFError ):
                        Canceled = True
                        break

                ClearWindow()
                chdir('../')

                if Canceled == False:
                    pdfName = filename + '.pdf'
                    MakePDF(ImageList=imgLoc, Filename=pdfName, DirLoc=dirLoc)
                    FinalInfo += f"{infoBanner} \"./{pdfName}\" 에 저장되었습니다.\n"

                else:
                    PrintInfo('다운로드가 취소되었습니다.')
                    break

                if Canceled == True:
                    PrintInfo('다운로드가 취소되었습니다.')
                    break

                    
            print()
            if FinalInfo.replace(' ', '') != "":
                print(FinalInfo, '\n')


        except ( KeyboardInterrupt, EOFError ):
            PrintInfo('다시 선택해주세요.')


def main():
    CheckInternet()
    ClearWindow()
    while True:
        try:
            PrintBanner()
            select = int(
                input(
                    '\n1. 만화 찾기'
                    '\n2. 만화 다운로드'
                    '\n3. 뒤로 가기'
                    '\n\n>> '
                )
            )

            if select == 1:
                mSearch()
            elif select == 2:
                mDownload()
            elif select == 3:
                ClearWindow() 
                break
            else:
                ClearWindow()
                PrintInfo('다시 선택해주세요.')

                
        except ( ValueError, KeyboardInterrupt, EOFError, NameError ):
            ClearWindow()
            PrintInfo('다시 선택해주세요.')
