# WoWsL NamuWiki Template UI

월드 오브 워쉽 레전드 함선 정보를 나무위키 표 양식으로 변환하는 Tkinter 도구입니다.

## EXE 다운로드 및 실행

Python 설치나 소스 빌드 없이 저장소의 [wowslnamu.zip](./wowslnamu.zip) 파일만 다운로드해서 사용할 수 있습니다.

1. `wowslnamu.zip`을 다운로드합니다.
2. ZIP 파일의 압축을 전부 해제합니다.
3. 압축을 푼 폴더에서 `wowslnamu\wowslnamu.exe`를 실행합니다.

`wowslnamu.exe`만 따로 옮기지 말고, 압축을 해제한 폴더 구조를 그대로 유지해야 합니다.

## 실행

Python 3.11 이상에서 다음 명령으로 실행합니다.

```powershell
python wowslnamu.py
```

## Windows EXE 빌드

Python.org 배포판 Python 3.11과 PyInstaller를 사용합니다.

```powershell
py -3.11 -m pip install -r requirements-build.txt
py -3.11 -m PyInstaller --clean --noconfirm .\wowslnamu.spec
```

완성된 실행 파일은 `dist\wowslnamu\wowslnamu.exe`에 생성됩니다. 배포할 때는 `wowslnamu` 폴더 전체를 함께 전달해야 합니다.
