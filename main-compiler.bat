pyinstaller -y -F -i ./ms.ico "main_downloader.py"

move dist/main_downloader.exe ../

rmdir /s /q build __pycache__ 

del /s /q main_downloader.spec

cd dist

move main_downloader.exe ../KDR-Integrated-Downloader.exe

cd ..

rmdir /s /q dist

exit