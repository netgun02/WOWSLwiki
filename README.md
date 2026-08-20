# WoWsL NamuWiki Template UI

월드 오브 워쉽 레전드 함선 정보를 나무위키 표 양식으로 변환하는 Tkinter 도구입니다.

## EXE 다운로드 및 실행

Python 설치나 소스 빌드 없이 다음 두 배포본 중 하나를 사용할 수 있습니다.

- [wowslnamu.exe](./wowslnamu.exe): 파일 하나만 내려받아 바로 실행하는 단일 파일 배포본
- [wowslnamu.zip](./wowslnamu.zip): 실행 속도와 파일 구성을 분리한 폴더형 배포본

ZIP 배포본은 다음 순서로 실행합니다.

1. `wowslnamu.zip`을 다운로드합니다.
2. ZIP 파일의 압축을 전부 해제합니다.
3. 압축을 푼 폴더에서 `wowslnamu\wowslnamu.exe`를 실행합니다.

`wowslnamu.exe`만 따로 옮기지 말고, 압축을 해제한 폴더 구조를 그대로 유지해야 합니다.

## 주요 변환 규칙

- 함선명은 `Ship Overview`의 `함선명 — 국가 • 티어 • 함종` 줄에서 대시 왼쪽을 추출합니다.
- `Legendary Tier`는 `전설` 티어로 변환하며, 본문에 등장하는 다른 함선의 `Tier IV` 같은 문장은 함선명으로 오인하지 않습니다.
- 부포 탭은 실제로 값이 있는 고유 부포 제원 수만큼 생성합니다. 빈 슬롯과 완전히 동일한 중복 제원은 제외하고, 같은 구경이라도 배치나 성능이 다르면 별도 탭으로 유지합니다.

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
py -3.11 -m PyInstaller --clean --noconfirm .\wowslnamu_onefile.spec
```

폴더형 실행 파일은 `dist\wowslnamu\wowslnamu.exe`, 단일 파일 실행본은 `dist\wowslnamu-onefile.exe`에 생성됩니다. 폴더형 배포본은 `wowslnamu` 폴더 전체를 함께 전달해야 합니다.
