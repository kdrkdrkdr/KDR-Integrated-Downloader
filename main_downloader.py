#-*- coding:utf-8 -*-

from multiprocessing import freeze_support, cpu_count, Pool
from signal import signal, SIGINT, SIG_IGN
from sys import exit as terminate
from click import clear as ClearWindow


from KDR_DOWNLOADER import ( 
    e_hentai_downloader, hiyobi_downloader, marumaru_downloader, 
    naver_wt_downloader, syosetu_downloader, toonkor_downloader,
    pixiv_downloader, 
)



DownloaderLIST = [
    e_hentai_downloader, hiyobi_downloader, marumaru_downloader, 
    naver_wt_downloader, syosetu_downloader, toonkor_downloader, 
    pixiv_downloader,
]


PrintInfo = lambda info: print(f"\n[KDR-통합다운로더] {info}\n")


def PrintBanner():
    print('''
    __ __ ____  ____ 
   / //_// __ \/ __ \\
  / ,<  / / / / /_/ /
 / /| |/ /_/ / _, _/ 
/_/ |_/_____/_/ |_|
  KDR-통합다운로더 ''')



def InitPool():
    signal(SIGINT, SIG_IGN)



if __name__ == "__main__":
    freeze_support()
    if cpu_count() == 1:
        Pool(1, InitPool)
    else:
        Pool(cpu_count() - 1, InitPool)

    ClearWindow()
    PrintBanner()
    while True:
        try:
            PrintInfo("종료하려면 Ctrl+C 를 누르세요.")
            select = int(
                input(
                    '\n1. E-Hentai 다운로더         '
                    '\n2. Hiyobi 다운로더           '
                    '\n3. Marumaru 다운로더         '
                    '\n4. NaverWebtoon 다운로더     '
                    '\n5. Syosetu 다운로더          '
                    '\n6. Toonkor 다운로더          '
                    '\n7. Pixiv 다운로더            '
                    '\n\n>> '
                )
            )

            if 0 < select < len(DownloaderLIST) + 1: 
                DownloaderLIST[select-1].main()
            else:
                ClearWindow()
                PrintInfo('다시 선택해주세요.')

                
        except ( ValueError, IndexError ):
            ClearWindow()
            PrintInfo('다시 선택해주세요.')


        except ( KeyboardInterrupt, EOFError ):
            ClearWindow()
            break
            
