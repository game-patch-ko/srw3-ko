제3차 슈퍼로봇대전 (SFC) 한글 패치  v0.9 (베타)
==================================================

슈퍼 패미컴용 「第3次スーパーロボット大戦」를 한국어로 옮기는 IPS 패치입니다.
게임 ROM은 들어 있지 않습니다. 직접 가지고 있는 원본 ROM에 패치를 적용해 쓰세요.


■ 들어 있는 파일

  srw3_ko.xdelta  한글 패치 (권장)
  srw3_ko.ips     한글 패치 (에뮬레이터 자동 적용용, 내용은 같음)
  README.txt      이 문서
  OFL.txt       글꼴 라이선스(SIL Open Font License 1.1) 전문과 저작권 표시


■ 적용할 원본 ROM

  파일    Dai-3-Ji Super Robot Taisen (J).smc
  형식    헤더 없음(512바이트 복사기 헤더가 없는 것), 1,572,864바이트
  CRC32   DFE9CC90

  ROM 파일이 1,573,376바이트라면 앞에 512바이트 헤더가 붙은 것입니다.
  헤더를 지운 다음 적용하세요.


■ 적용 방법

  1. 원본 ROM을 복사해 둡니다(원본은 그대로 남겨 두세요).
  2. srw3_ko.xdelta를 복사본에 적용합니다.
     - 웹: Rom Patcher JS (https://www.marcrobledo.com/RomPatcher.js/)
     - Windows 프로그램: Delta Patcher
     - 명령줄: xdelta3 -d -s 원본.smc srw3_ko.xdelta srw3_ko.smc
  3. 결과 ROM은 2MB(2,097,152바이트)이고 CRC32는 AEDB3DCB입니다.
     만든 ROM을 에뮬레이터에서 바로 엽니다.

  IPS를 쓰는 경우: Mesen, snes9x 등은 ROM과 같은 폴더에 같은 이름의 .ips가 있으면
  실행할 때 자동으로 적용합니다(예: srw3.smc + srw3.ips). Flips 등으로 직접 적용해도 됩니다.
  단, IPS는 헤더 붙은 ROM에도 오류 없이 적용되어 망가진 ROM을 만들므로 크기를 꼭 확인하세요.
  xdelta는 원본이 다르면 오류를 내고 멈춥니다.


■ 번역 범위

  - 대사 전체, 프롤로그·엔딩 문장
  - 파일럿·유닛·무기 이름, 지형, 메뉴와 창 문구
  - 스테이지 도입 제목(「제1화 『암운』」 등), 타이틀 로고(「제3차 슈퍼로봇대전」)
  - 타이틀 화면의 START / CONTINUE / LOAD는 영어 그대로 두었습니다.


■ 알려진 문제

  - 일부 창에서 긴 이름이나 문구가 창 테두리에 닿거나 살짝 넘칠 수 있습니다.
  - 확인한 에뮬레이터: Mesen2 2.1.1. 실기와 다른 에뮬레이터에서는 확인하지 않았습니다.
  - 엔딩 화면과 사운드 테스트 곡명은 실제 진행으로 확인하지 못했습니다.
  - 기존 세이브와 상태 저장은 원본 ROM과 섞어 쓰지 마세요.

  이상한 화면이나 오역을 발견하면 화면 사진과 함께 알려 주세요.


■ 표기

  - 이름은 국내에 널리 쓰이는 표기를 따르되, 게터로보는 「게타」로 적었습니다.
  - 무기·기술 이름은 붙여 씁니다(예: 갓브레이커, 로켓펀치).


■ 글꼴

  한글은 나눔고딕(대사·메뉴 12px, 스테이지 제목 15px)과 나눔스퀘어 ExtraBold(타이틀 로고)를
  흑백 비트맵으로 변환해 넣었습니다. 두 글꼴은 NAVER(구 NHN)가 SIL Open Font License 1.1로
  배포합니다. 저작권 표시와 라이선스 전문은 OFL.txt에 있습니다.


■ 권리

  「제3차 슈퍼로봇대전」과 등장 작품·캐릭터의 권리는 각 권리자에게 있습니다.
  이 패치는 비공식 팬 번역이며, 권리자와 관계가 없습니다. 패치 파일만 배포하며 ROM은 배포하지 않습니다.


■ AI 사용 고지

  이 프로젝트는 Anthropic의 AI 모델인 Claude를 이용해 작성·개발되었습니다.
  책임은 작성자에게 있으며, Claude는 도구일 뿐 저작자나 기여자가 아닙니다.

  This project was written and developed using Claude, an AI model by Anthropic.
  The author is responsible for it; Claude is a tool and not an author or contributor.
