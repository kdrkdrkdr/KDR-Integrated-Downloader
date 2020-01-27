#-*-coding:utf-8 -*-

from bs4 import BeautifulSoup
from requests import get, exceptions
from reportlab.pdfgen.canvas import Canvas
from signal import signal, SIGINT, SIG_IGN
from ping3 import ping
from sys import exit as terminate
from shutil import rmtree
from os import mkdir, chdir
from PIL.Image import open as IMGOPEN
from re import sub
from click import clear as ClearWindow
from threading import Thread
from queue import Queue


baseURL = "https://comic.naver.com"

hParser = 'html.parser'

infoBanner = "[Naver-WebToon-Downloader]"

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
마지막 수정 날짜 : 2020/01/15
제작자 : kdr (https://github.com/kdrkdrkdr/)
      .-. .-.  .--.  .-. .-..----..----.            
      |  `| | / {} \ | | | || {_  | {}  }           
      | |\  |/  /\  \\ \_/ /| {__ | .-. \           
      `-' `-'`-'  `-' `---' `----'`-' `-'           
.-. . .-..----..----.  .---.  .----.  .----. .-. .-.
| |/ \| || {_  | {}  }{_   _}/  {}  \/  {}  \|  `| |
|  .'.  || {__ | {}  }  | |  \      /\      /| |\  |
`-'   `-'`----'`----'   `-'   `----'  `----' `-' `-'
         Naver WebToon Downloader by kdr
''')



def PrintProgressBar(iteration, total, prefix='', suffix='', decimals=1, length=50, fill='#'):
    percent = ("{0:." + str(decimals) + "f}").format(100 * (iteration / float(total)))
    filledLength = int(length * iteration // total)
    bar = fill * filledLength + ' ' * (length - filledLength)
    print(f'\r{prefix} |{bar}| {percent}% {suffix}', end='\r')
    if iteration == total: 
        print()


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
            html = get(url, headers=header).text
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
                resp = get(url, headers=header, ).content
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



def GetIMGsURL(EpisURL):
    soup = FastGetSoup(EpisURL).find('div', {'class':'wt_viewer'}).find_all('img')
    ListOfIMGsURL = [i['src'] for i in soup]
    return ListOfIMGsURL



def WebToonSearch():
    while True:
        try:
            kWord = str(input("검색할 만화 이름을 입력하세요. (exit 입력하면 검색종료) : ")).replace(' ', '')
            if kWord.lower() == 'exit': ClearWindow(); break
            sPage = int(input("몇쪽까지 검색할까요? (0을 입력하면 검색종료) : "))
            if sPage == 0: ClearWindow(); break
            
            for i in range(1, sPage+1):
                soup = FastGetSoup(f"{baseURL}/search.nhn?m=webtoon&keyword={kWord}&type=title&page={i}")
                rContainer = soup.find('ul', {'class':'resultList'}).find_all('h5')

                if rContainer == []:
                    PrintInfo("검색 결과가 없습니다.")
                    break

                else:
                    PrintInfo(f"{i}페이지 검색 결과입니다.")
                    for j in rContainer:
                        wTitle = j.a.text
                        wLink = baseURL + j.a['href']
                        print('-'*80)
                        print("제목 : ", wTitle)
                        print("링크 : ", wLink)

                print('-'*80, '\n')

        except ( TypeError, KeyboardInterrupt, EOFError, UnboundLocalError):
            ClearWindow()
            PrintInfo("다시 입력해주세요.")



def WebToonDownload():
    while True:
        while True:
            try:
                wLink = str(input("다운로드할 웹툰의 링크를 입력하세요. (exit 입력하면 다운로드 종료) : ")).replace(' ', '')
                if wLink.lower() == 'exit':
                    ClearWindow()
                    return

                elif not baseURL+'/webtoon/list.nhn?titleId=' in wLink:
                    ClearWindow()
                    PrintInfo("잘못된 URL입니다."); 
                    break

                else:
                    soup = FastGetSoup(wLink)
                    epiCount = int(str(soup.find('td', {'class':'title'}).a['onclick']).split("\'")[-2])
                    pageCount = (epiCount // 10) + 1

                    epiList = []
                    for i in range(1, pageCount+1, 1):
                        wtEpis = FastGetSoup(wLink + f'&page={i}').find_all('td', {'class':'title'})
                        for w in wtEpis:
                            epiList.append([w.a.text, baseURL + w.a['href']])
                    
                    print()
                    epiList.reverse()
                    for epi in enumerate(epiList):
                        print("-"*80, f"\n{epi[0]+1}. {epi[1][0]}")
                    print("-"*80, '\n')

                    wtInfo = soup.find('div', {'class':'comicinfo'})

                    wAuthor = wtInfo.find('span', {'class':'wrt_nm'}).text.strip()
                    wTitle = wtInfo.find('img')['title']
                    wIntro = wtInfo.find('p').text.strip()
                    wGenre = wtInfo.find('span', {'class':'genre'}).text.strip()

                    sIndex = str(input("""
다운로드 받고 싶은 횟차를 입력하세요. (exit 입력하면 다운로드 종료)
(사용법) 1화 ~ 10화, 12화 모두 다운로드 : 1~10, 12 
: """)).replace(' ', '').split(',')
                    if sIndex == 'exit':
                        ClearWindow(); break

                    episode = []
                    for e in sIndex:
                        if '~' in e:
                            s = e.split('~')

                            s1 = int(s[0])
                            s2 = int(s[1])

                            if s1 <= s2: InDe = 1
                            else: InDe = -1

                            section = list(range(int(s[0]), int(s[1])+InDe, InDe))

                        else:
                            section = [int(e)]

                        episode.extend(section)


                    FinalInfo = ""
                    Canceled = False

                    for epi in episode:
                        try:
                            epiTitle = epiList[epi-1][0]
                            epiLink = epiList[epi-1][1]
                        except ( IndexError ):
                            PrintInfo(f"{epi}화는 잘못된 횟차 수 입니다.")
                            break


                        epiIMGsURL = GetIMGsURL(epiLink)
                        fname = sub('[\/:*?"<>|]', ' ', f"{wTitle}_{epiTitle}")
                        dirLoc = f"./{fname}/"
                        imgLoc = []

                        MakeDirectory(dirLoc)

                        ClearWindow()
                        print(f'\n제목 : {wTitle}'
                            + f'\n\n작가 : {wAuthor}'
                            + f'\n\n횟차 : {epi}화'
                            + f'\n\n{wIntro}\n')


                        for epiIMG in enumerate(epiIMGsURL):
                            try:
                                PrintProgressBar(epiIMG[0], len(epiIMGsURL), prefix=f'{infoBanner}', suffix=f'({epiIMG[0]}/{len(epiIMGsURL)})')
                                imgName = f'{fname} {epiIMG[0]+1}.jpg'
                                FastDownload(imgName, epiIMG[1])
                                imgLoc.append(f"{dirLoc}{imgName}")

                            except ( KeyboardInterrupt, EOFError ):
                                Canceled = True
                                break

                        ClearWindow()
                        chdir('../')

                        if Canceled == False:
                            MakePDF(imgLoc, f"./{fname}.pdf", dirLoc)
                            FinalInfo += f"{infoBanner} \"./{fname}.pdf\" 에 저장되었습니다.\n"

                        else:
                            rmtree(dirLoc, ignore_errors=True)
                            PrintInfo('다운로드가 취소되었습니다.')
                            break

                    print()
                    if FinalInfo.replace(' ', '') != "":
                        print(FinalInfo, '\n')


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
                    '\n1. 웹툰 찾기'
                    '\n2. 웹툰 다운로드'
                    '\n3. 뒤로 가기'
                    '\n\n>> '
                )
            )

            if select == 1:
                WebToonSearch()
            elif select == 2:
                WebToonDownload()
            elif select == 3:
                ClearWindow() 
                break
            else:
                ClearWindow()
                PrintInfo('다시 선택해주세요.')

                
        except ( ValueError, KeyboardInterrupt, EOFError, NameError ):
            ClearWindow()
            PrintInfo('다시 선택해주세요.')