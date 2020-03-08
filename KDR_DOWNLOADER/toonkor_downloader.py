#-*-coding:utf-8 -*-

from bs4 import BeautifulSoup
from base64 import b64decode
from requests import get, exceptions
from img2pdf import convert as pdfConvert
from signal import signal, SIGINT, SIG_IGN
from ping3 import ping
from sys import exit as terminate, stdout
from shutil import rmtree
from os.path import join
from os import mkdir, chdir, walk
from zipfile import ZipFile
from PIL.Image import open as IMGOPEN
from re import sub
from click import clear
from threading import Thread
from queue import Queue


baseURL = "https://toonkor.fyi"

header = {
    'User-agent' : 'Mozilla/5.0',
    'Referer' : baseURL,
}

hParser = 'html.parser'

infoBanner = "[Toonkor-Downloader]"

genreList = [
    '성인', '드라마', '판타지', '액션',
    '로맨스', '일상', '개그', '미스터리',
    '순정', '스포츠', 'BL', '스릴러', 
    '무협', '학원', '공포', '스토리'
]

consoList = {
    'ㄱ':'ga', 'ㄴ':'na', 'ㄷ':'da', 'ㄹ':'la',
    'ㅁ':'ma', 'ㅂ':'ba', 'ㅅ':'sa', 'ㅇ':'aa',
    'ㅈ':'ja', 'ㅊ':'ca', 'ㅋ':'ka', 'ㅌ':'ta',
    'ㅍ':'pa', 'ㅎ':'ha', 'e':'en', 'n':'nu'
}

PrintInfo = lambda info: print(f"{infoBanner} {info}\n")


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
마지막 수정 날짜 : 2020/03/09
제작자 : kdr (https://github.com/kdrkdrkdr/)
 ______               __ ______  ___ 
/_  __/__  ___  ___  / //_/ __ \/ _ \\
 / / / _ \/ _ \/ _ \/ ,< / /_/ / , _/
/_/  \___/\___/_//_/_/|_|\____/_/|_| 
        ToonKor Downloader
''')



def PrintProgressBar(iteration, total, prefix='', suffix='', decimals=1, length=50, fill='#'):
    percent = ("{0:." + str(decimals) + "f}").format(100 * (iteration / float(total)))
    filledLength = int(length * iteration // total)
    bar = fill * filledLength + ' ' * (length - filledLength)
    print(f'\r{prefix} |{bar}| {percent}% {suffix}', end='\r')
    if iteration == total: 
        print()



def MakeZIP(directory, ZipName):
    JPGPath = []
    for root, directories, files in walk(directory):
        for filename in files:
            filepath = join(root, filename)
            JPGPath.append(filepath)
    
    with ZipFile(ZipName, 'w') as z:
        for jpg in JPGPath:
            z.write(jpg)



def GetIMGsSize(imgPath):
    while True:
        try:
            img = IMGOPEN(imgPath)
            return img.size
        except:
            continue

def MakePDF(ImageList, Filename, DirLoc):
    try:
        with open(Filename, 'wb') as pdf:
            pdf.write(pdfConvert(ImageList))
    except:
        PrintInfo('PDF 제작에 오류가 발생했습니다.')
    
    finally:
        rmtree(DirLoc, ignore_errors=True)


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



def GetMangaName(bfSoup):
    mElement = bfSoup.find_all('div', {'class':'list-row'})
    mList = [m.find('div', {'class':'section-item-inner'})['alt'] for m in mElement]
    return mList



def GetIMGsURL(EpisURL):
    ListOfIMGsURL = []

    soup = FastGetSoup(EpisURL)

    b64Code = soup.text.split("var toon_img = ")[1].split(";")[0]
    html = b64decode(b64Code.encode("UTF-8")).decode("UTF-8")
    IMGsCode = BeautifulSoup(html, hParser).find_all("img")

    for imgURL in IMGsCode:
        imgSrc  = imgURL['src']

        if len(imgSrc.split('/data/')[0].replace(' ', '')) != 0:
            ListOfIMGsURL.append(imgSrc)
        else:
            ListOfIMGsURL.append(baseURL + imgSrc)

    return ListOfIMGsURL



def ToonSearch():
    while True:
        try:
            nSelect = int(
                input(
                    '\n1. 만화 이름으로 검색하기'
                    '\n2. 장르로 검색하기'
                    '\n3. 완결 작품 검색하기'
                    '\n4. 뒤로가기'
                    '\n\n>> '
                )
            )
            if nSelect == 1:
                while True:
                    try:
                        kWord = str(input("검색할 만화 이름을 입력하세요. (exit 입력하면 검색종료) : ")).replace(' ', '')
                        if kWord.lower() == 'exit': clear(); break
                        sURL = f"{baseURL}/bbs/search.php?sfl=wr_subject%7C%7Cwr_content&stx={kWord}"
                        soup = FastGetSoup(sURL)

                        while True:
                            try:
                                lstContainer = soup.find('div', {'class':'list-container'}).find_all('div', {'class':'section-item-title'})
                                if lstContainer == []:
                                    PrintInfo("검색결과가 없습니다.")
                                break
                            
                            except ( AttributeError ):
                                continue
                        

                        print('\n')
                        for lstC in lstContainer:
                            
                            mTitle = lstC.find('h3').text
                            mLink = lstC.find('a')['href']
                            print('-'*80)
                            print("제목 : ", mTitle)
                            print("링크 : ", baseURL + mLink)
                        print('-'*80, '\n')
                        
                    except ( ValueError, EOFError, KeyboardInterrupt ):
                        PrintInfo("다시 입력해주세요.\n")
            
            
            elif nSelect == 2:
                while True:
                    try:
                        gSelect = str(
                            input(
                                '\n검색하고 싶은 만화의 장르를 입력하세요. (exit을 입력하면 검색종료)'
                                f"\n\n{genreList}"
                                '\n\n>> '
                            )
                        ).replace(' ', '')

                        if gSelect == 'exit': clear(); break 

                        elif gSelect in genreList:
                            soup = FastGetSoup(f"{baseURL}/웹툰/연재?fil={gSelect}")
                            print(GetMangaName(soup))
                            
                        else:
                            PrintInfo("다시 입력해주세요.\n")
                            
                    except ( EOFError, KeyboardInterrupt ):
                        PrintInfo("다시 입력해주세요.\n")


            elif nSelect == 3:
                while True:
                    try:
                        cSelect = str(
                            input(
                                '\n검색하고 싶은 완결 만화의 초성을 입력하세요. (exit 입력하면 검색종료)'
                                '\n초성:ㄱ~ㅎ, 영어:e, 숫자:n 입력'
                                '\n\n>> '
                            )
                        ).lower().replace(' ', '')

                        if cSelect == 'exit': clear(); break

                        elif len(cSelect) != 1: PrintInfo("한 글자만 입력하세요.\n")

                        elif cSelect in [i for i in consoList]:
                            soup = FastGetSoup(f"{baseURL}/웹툰/완결/{consoList[cSelect]}")
                            print(GetMangaName(soup))

                        else:
                            PrintInfo("다시 입력해주세요.\n")

                    except ( EOFError, KeyboardInterrupt ):
                        PrintInfo("다시 입력해주세요.\n")

            elif nSelect == 4: return

            else:
                PrintInfo("다시 입력해주세요.\n")

        except ( ValueError, EOFError, KeyboardInterrupt ):
            PrintInfo("다시 입력해주세요.\n")    



def ToonDownload():
    while True:
        while True:
            Link = str(input("다운로드할 만화의 링크를 입력하세요. (exit 입력하면 다운로드 종료) : ")).replace(' ', '')
            if Link == 'exit': return

            while True:
                soup = FastGetSoup(Link)
                try:
                    
                    table = list(soup.find('table', {'class':'web_list'}).find_all('tr', {'class':'tborder'}))
                    table.reverse()
                    break
                except ( AttributeError, TypeError ):
                    continue
            
            epiList = []
            e_count = 0
            for t in table:                
                epiIndex = t.find('td', {'class':'episode__index'})
                epiTitle = epiIndex['alt']
                epiTitle = sub('[\/:*?"<>|]', '_', epiIndex['alt'])
                epiURL = baseURL + epiIndex['data-role']

                epiList.append([epiTitle, epiURL])
                e_count += 1
                print("-"*80, f"\n{e_count}. {epiTitle}")
            print("-"*80, '\n')

            
            title = soup.find('td', {'class':'bt_title'}).text
            author = soup.find('span', {'class':'bt_data'}).text
            intro = soup.find('td', {'class':'bt_over'}).text


            sIndex = str(input("""
다운로드 받고 싶은 횟차를 입력하세요. (exit 입력하면 다운로드 종료)
(사용법) 1화 ~ 10화, 12화 모두 다운로드 : 1~10, 12 
: """)).replace(' ', '').split(',')
            if sIndex == 'exit': clear(); break

            fType = str(input("저장할 파일 형태를 입력하세요. (zip 또는 pdf 입력, 기본값은 zip) : ")).replace(' ', '')

            if fType != "pdf":
                fType = "zip"


            episode = []
            isPlus = False

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
                
                dirLoc = f"./{epiTitle}/"
                imgLoc = []

                MakeDirectory(dirLoc)
                
                clear()
                print(f'\n제목 : {title}'
                    + f'\n\n작가 : {author}'
                    + f'\n\n횟차 : {epi}화'
                    + f'\n\n{intro}\n')

                i_count = 0
                for epiIMG in epiIMGsURL:
                    try:
                        PrintProgressBar(i_count, len(epiIMGsURL), prefix=f'{infoBanner}', suffix=f'({i_count}/{len(epiIMGsURL)})')
                        imgName = f'{epiTitle} {i_count+1}.jpg'
                        FastDownload(imgName, epiIMG)
                        imgLoc.append(f"{dirLoc}{imgName}")
                        i_count += 1

                    except ( KeyboardInterrupt, EOFError ):
                        Canceled = True
                        break

                clear()
                chdir('../')
                
                if Canceled == False:
                    if fType == 'pdf':
                        MakePDF(imgLoc, f"./{epiTitle}.pdf", dirLoc)
                        FinalInfo += f"{infoBanner} \"./{epiTitle}.pdf\" 에 저장되었습니다.\n"
                        
                    else:
                        MakeZIP(dirLoc, f'./{epiTitle}.zip')
                        FinalInfo += f"{infoBanner} \"./{epiTitle}.zip\" 에 저장되었습니다.\n"

                rmtree(dirLoc, ignore_errors=True)


                if Canceled == True:
                    PrintInfo('다운로드가 취소되었습니다.')
                    break

                
            print()
            if FinalInfo.replace(' ', '') != "":
                print(FinalInfo, '\n')



def main():
    while True:
        try:
            clear()
            CheckInternet()
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
                ToonSearch()
            elif select == 2:
                ToonDownload()
            elif select == 3:
                clear(); 
                break
            else:
                PrintInfo('다시 선택해주세요.'); continue
                
        except ( ValueError, KeyboardInterrupt, EOFError, NameError ):
            PrintInfo('다시 선택해주세요.')