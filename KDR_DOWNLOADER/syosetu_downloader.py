#-*- coding:utf-8 -*-

from bs4 import BeautifulSoup
from requests import get, exceptions
from os import getcwd, mkdir, chdir
from shutil import rmtree
from console_progressbar import ProgressBar
from colorama import init
from sys import exit as terminate

header = {'User-agent' : 'Mozilla/5.0'}
baseURL = "https://ncode.syosetu.com"
sWordExit = ['', 'exit', 0]

GetSoup = lambda url_addr: BeautifulSoup(get(url_addr, headers=header).text, 'html.parser', from_encoding='cp949')

ClearWindow = lambda: print("\x1B[2J", end="")

PrintInfo = lambda info: print("\n[Syosetu-Downloader] {} \n".format(info))

def PrintBanner():
    print('''
最後の修整日 : 2019/10/07
製作者 : kdr (https://github.com/kdrkdrkdr/)
 _____                      _                              
/  ___|                    | |                             
\ `--. _   _  ___  ___  ___| |_ _   _   ___ ___  _ __ ___  
 `--. \ | | |/ _ \/ __|/ _ \ __| | | | / __/ _ \| '_ ` _ \ 
/\__/ / |_| | (_) \__ \  __/ |_| |_| || (_| (_) | | | | | |
\____/ \__, |\___/|___/\___|\__|\__,_(_)___\___/|_| |_| |_|
        __/ |                                              
       |___/                                                                                             
                       小説ダウンロード
    \n''')

def PrintStatus(SyosetuInfo, AllList, Status):
    prgsbar = ProgressBar(
        total=AllList, 
        prefix="ダウンロード : ", 
        suffix=" ({}/{})\n".format(Status, AllList),
        decimals=2, 
        length=50, 
        fill="#", 
        zfill=" ")
    ClearWindow()
    print(SyosetuInfo)
    prgsbar.print_progress_bar(Status)

def Search():
    while True:
        try:
            select = int(
                input(
                    "\n1. 月間ランキングトップ"
                    "\n2. 検索語"
                    "\n3. 後回し"
                    "\n\n検索する方法を選択してください。 : "
                )
            )
            if select == 1:
                rank = int(input("何番目まで検索しましょうか。 (1~300) : "))
                rankSoup = GetSoup("https://yomou.syosetu.com/rank/list/type/monthly_total/")
                Point = rankSoup.find_all('span', {'class':'attention'})
                
                ClearWindow()
                for i in range(rank):
                    sInfo = rankSoup.find('a', {'id':'best{}'.format(i+1)})
                    
                    sTitle = sInfo.text
                    sLink = sInfo['href']
                    sPoint = Point[i].text

                    print("-"*100, '\n')
                    print(str(i+1) + "位")
                    print("題目 : " + sTitle)
                    print("リンク : " + sLink)
                    print("ポイント : " + sPoint)

                print("\n", "-"*100)

            elif select == 2:
                while True:
                    try:
                        sWord = str(input("\n検索語を入力してください。(exitを入力すると検索終了) : "))
                        if sWord.replace(' ', '').lower() in sWordExit: break
                        sPage = int(input("\n何ページまで探してみましょうか。(0を入力すると、検索終了) : "))
                        if sPage <= 0: break

                        for p in range(sPage):
                            sSoup = GetSoup('https://yomou.syosetu.com/search.php?search_type=novel&word={}&search_type=novel&p={}'.format(sWord, p))
                            try:
                                ClearWindow()
                                searchKekka = sSoup.find('div', {'id':'main_search'}).find_all('div', {'class':'searchkekka_box'})
                                for sk in searchKekka:
                                    skTitle = sk.find('a').text
                                    skLink = sk.find('a')['href']

                                    skInfo = sk.table.find_all('td')[1].find_all('a')
                                    skContent = sk.find('div', {'class':'ex'}).text

                                    print("\n" + "-"*100)
                                    print("\n題目 : " + skTitle)
                                    print("\nリンク : " + skLink)
                                    print("\n", skContent)

                                print("\n", "-"*100)

                            except AttributeError:
                                PrintInfo('検索結果がありません。')
                    
                    except ( ValueError, EOFError, KeyboardInterrupt, UnboundLocalError, NameError ):
                        PrintInfo('もう一度入力してください。')

            elif select == 3:
                ClearWindow()
                break

            else:
                PrintInfo("もう一度選択してください。")

        except ( KeyboardInterrupt, EOFError, ValueError ):
            PrintInfo("もう一度選択してください。")

def Download():
    while True:
        try:
            while True:
                syosetuLink = str(input('ダウンロードする小説アドレスを入力してください。(exit 入力するとダウンロード終了) : '))
                if syosetuLink.replace(' ', '').lower() == 'exit':
                    ClearWindow(); return

                elif not baseURL in syosetuLink: 
                    PrintInfo('間違ったURLです。') 
                
                else:
                    break

            soup = GetSoup(syosetuLink)

            bigTitle = soup.find('p', {'class':'novel_title'}).text
            index = soup.find('div', {'class':'index_box'}).find_all('dl')
            author = soup.find('div', {'class':'novel_writername'}).find('a').text

            try:
                mkdir('{}'.format(bigTitle))

            except FileExistsError:
                rmtree('{}'.format(bigTitle), ignore_errors=True)
                mkdir('{}'.format(bigTitle))

            finally:
                chdir('{}'.format(bigTitle))

            count = 0

            info = ""
            info += (
                "題目 : {} \n\n".format(bigTitle)
                + "作家 : {} \n\n".format(author)
                + "回次数 : {} \n\n".format(len(index))
            )
            Canceled = False
            for i in index:
                try:
                    nURL = baseURL + i.find('a')['href']
                    nTitle = i.find('a').text

                    nSoup = GetSoup(nURL)
                    nContent = nSoup.find('div', {'id':'novel_honbun'}).find_all('p')

                    novelContent = ""
                    for nC in nContent:
                        novelContent += str(nC.text) + "\n"

                    PrintStatus(info, len(index), count)
                    
                    count += 1
                    with open('{}_{}.txt'.format(count, nTitle), 'w', encoding="utf-8") as f:
                        f.write(novelContent)
                        
                except ( KeyboardInterrupt, EOFError ):
                    Canceled = True
                    break
            
            ClearWindow()
            chdir('../')
            
            if Canceled == False:
                CurrentDIR = '"{}\\{}"'.format(getcwd(), bigTitle)
                PrintInfo(CurrentDIR + ' にダウンロードされた。')

            if Canceled == True: 
                PrintInfo('ダウンロードが中止されました。')
                rmtree(bigTitle, ignore_errors=True)

        except ( KeyboardInterrupt, EOFError ):
            PrintInfo('もう一度入力してください。')
            


def main():
    init()
    ClearWindow()

    while True:
        try:
            PrintBanner()
            select = int(
                input(
                    '\n1. 小説探し'
                    '\n2. 小説ダウンロード'
                    '\n3. プログラム終了'
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
                PrintInfo('もう一度選択してください。'); continue
                
        except ( ValueError, KeyboardInterrupt, EOFError ):
            PrintInfo('もう一度選択してください。')