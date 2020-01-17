from multiprocessing import freeze_support, cpu_count, Pool
from signal import signal, SIGINT, SIG_IGN
from sys import exit as terminate
from click import clear as ClearWindow

import e_hentai_downloader
import hiyobi_downloader
import marumaru_downloader
import naver_wt_downloader
import syosetu_downloader
import ToonkorDownloader


def InitPool():
    signal(SIGINT, SIG_IGN)

PrintInfo = lambda info: print(f"\n[KDR-통합다운로더] {info}\n")


if __name__ == "__main__":
    freeze_support()
    if cpu_count() == 1:
        Pool(1, InitPool)
    else:
        Pool(cpu_count() - 1, InitPool)

    ClearWindow()
    while True:
        try:
            PrintInfo('')
            select = int(
                input(
                    '\n1. E-Hentai 다운로더'
                    '\n2. Hiyobi 다운로더'
                    '\n3. Marumaru 다운로더'
                    '\n4. NaverWebtoon 다운로더'
                    '\n5. Syosetu 다운로더'
                    '\n6. Toonkor 다운로더'
                    '\n7. 프로그램 종료'
                    '\n\n>> '
                )
            )

            if select == 1:
                e_hentai_downloader.main()
            elif select == 2:
                hiyobi_downloader.main()
            elif select == 3:
                marumaru_downloader.main()
            elif select == 4:
                naver_wt_downloader.main()
            elif select == 5:
                syosetu_downloader.main()
            elif select == 6:
                ToonkorDownloader.main()
            elif select == 7:
                terminate()
            else:
                PrintInfo('다시 선택해주세요.')

                
        except ( ValueError, KeyboardInterrupt, EOFError, NameError ):
            ClearWindow()
            PrintInfo('다시 선택해주세요.')