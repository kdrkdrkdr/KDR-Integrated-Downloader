from ping3 import ping
from requests import get, exceptions
from signal import signal, SIGINT, SIG_IGN
from json import loads
from re import sub
from os import mkdir, chdir
from shutil import rmtree
from multiprocessing import Pool, freeze_support, cpu_count
from sys import exit as terminate
from click import clear as ClearWindow
from bs4 import BeautifulSoup
from keyboard import read_key
from threading import Thread
from queue import Queue


enableProxy = False
enableRemoteDNS = True

proxyAddr = "127.0.0.1"
proxyPort = "1080"


if not enableProxy:
    proxy = {}

else:
    if enableRemoteDNS:
        proxy = {
            'http': "socks5h://" + proxyAddr + ":" + proxyPort,
            'https': "socks5h://" + proxyAddr + ":" + proxyPort
        }
    else:
        proxy = {
            'http': "socks5://" + proxyAddr + ":" + proxyPort,
            'https': "socks5://" + proxyAddr + ":" + proxyPort
        }


headers = {
        'User-agent' : 'Mozilla/5.0',
        "cookie": "",
        "Referer" : 'https://www.pixiv.net'
}

hParser = "html.parser"

PrintInfo = lambda info: print(f"\n[Pixiv-Downloader] {info}")


def PrintBanner():
    print('''
   ___ _      _       
  / _ (_)_  _(_)_   __
 / /_)/ \ \/ / \ \ / /
/ ___/| |>  <| |\ V / 
\/    |_/_/\_\_| \_/  
   Pixiv Downloader
    ''')


    
def CheckInternet():
    try:
        if ping('8.8.8.8') == None:
            terminate('인터넷 연결 또는 서버가 내려갔는지 확인하세요.')
    except ( OSError ):
        terminate('리눅스 사용자는 root권한을 이용해주세요.')

def GetSoup(queue, url):
    while True:
        try:
            html = get(url, headers=headers).text
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
                resp = get(url, headers=headers, ).content
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



def IMGsDownload(artIdList):
    for artID in artIdList:
        try:
            fname = './' + artID + '.png'

            illustURL = f"https://www.pixiv.net/ajax/illust/{artID}"
            illustJsonContent = loads(get(illustURL, headers=headers, proxies=proxy).text)
            
            if illustJsonContent['error'] == True:
                PrintInfo("일러스트를 찾을 수 없습니다!")
                continue

            else:
                illustURL = illustJsonContent['body']['urls']['original']
                FastDownload(f'{fname}', illustURL)
                PrintInfo(f"'{fname}' 에 저장되었습니다.")

        except (EOFError, KeyboardInterrupt):
            rmtree(f'{fname}', ignore_errors=True)
            PrintInfo("다운로드가 중지되었습니다.")
            return
            



def FindTAGs(tagName, pageNum):
    tagDict = {}
    jsonSearch = loads(FastGetSoup(f'https://api.imjad.cn/pixiv/v1/?type=search&word={tagName}&mode=tag&page={pageNum}').text)

    for i in jsonSearch['response']:
        artTitle = i['title']
        artURL = 'https://www.pixiv.net/artworks/' + str(i['id'])
        tagDict[artTitle] = artURL
        
    return tagDict



def PixivSearch():
    kWord = str(input("찾고싶은 Pixiv 작품의 태그를 검색하세요. : "))
    page = 1

    while True:
        tags = FindTAGs(kWord, page)
        for title in tags:
            print('-'*80)
            print("제목 : ", title)
            print("링크 : ", tags[title])
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
                    return

                if rk in ['down', 'up', 'esc']:
                    break

            except ( KeyboardInterrupt, EOFError ):
                PrintInfo("다시 입력해주세요.")



def PixivDownload():
    while True:
        try:
            select = int(
                input(
                    '\n1. 작품 링크로 다운로드'
                    '\n2. 작품 태그로 다운로드'
                    '\n3. 뒤로 가기'
                    '\n\n>> '
                )
            )

            if select == 1:
                try:
                    print("\n',' 로 작품 구분합니다.\n")
                    artLinkList = str(input('다운로드 할 작품의 Pixiv 작품 링크를 입력하세요. : ')).split(',')
                    artIDs = [sub('[\D]', '', i) for i in artLinkList]
                    IMGsDownload(artIdList=artIDs)
                except ( KeyboardInterrupt, EOFError ):
                    ClearWindow()
                    break
            

            elif select == 2:
                try:
                    artTag = str(input('다운로드할 작품의 태그를 입력하세요. : '))
                    artPage = int(input('몇 페이지 가량 다운로드 할까요? : '))
                    
                    for p in range(artPage):
                        tags = FindTAGs(artTag, artPage)
                        artIDs = [sub('\D', '', tags[t]) for t in tags]
                        IMGsDownload(artIdList=artIDs)

                except ( UnboundLocalError, TypeError, KeyboardInterrupt, EOFError ):
                    PrintInfo("다시 입력해주세요.")


            elif select == 3:
                ClearWindow()
                break


            else:
                PrintInfo("다시 선택해주세요.")


        except ( KeyboardInterrupt, EOFError ):
            ClearWindow()
            return

        except ( TypeError ):
            PrintInfo("다시 선택해주세요.")




def main():
    CheckInternet()
    ClearWindow()
    PrintBanner()
    while True:
        try:
            select = int(
                input(
                    '\n1. 작품 찾기'
                    '\n2. 작품 다운로드'
                    '\n3. 뒤로 가기'
                    '\n\n>> '
                )
            )

            if select == 1:
                PixivSearch()

            elif select == 2:
                PixivDownload()
            
            elif select == 3:
                ClearWindow() 
                break
            else:
                ClearWindow()
                PrintInfo('다시 선택해주세요.')

                
        except ( ValueError, KeyboardInterrupt, EOFError, NameError ):
            ClearWindow()
            PrintInfo('다시 선택해주세요.')
