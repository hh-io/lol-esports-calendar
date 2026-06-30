# lol-esports-calendar

[简体中文](README.md) · [English](README.en.md) · **한국어**

**리그 오브 레전드 e스포츠 경기 일정**(**LPL / LCK / LEC / LCP / LTA / MSI / Worlds / 국제 대회**)을 자동으로 수집해 구독 가능한 `.ics` 캘린더 파일을 생성합니다. **Apple 캘린더, Google 캘린더, Outlook** 등 iCalendar(`.ics`) 구독을 지원하는 모든 클라이언트에서 사용할 수 있습니다. GitHub Actions가 매시간 갱신하고 GitHub Pages에서 호스팅합니다. **순수 표준 라이브러리, 의존성 없음.**

캘린더 본문은 중국어 / 영어 / 한국어를 지원합니다(아래 표 참고).

## 구독 링크

아래 링크를 복사해 구독하세요(캘린더 본문은 **한국어**). 중국어 / 영어가 필요하면 페이지 상단의 **简体中文 / English** 전환을 사용하세요.

| 지역 | 구독 URL |
|------|----------|
| LPL (중국) | `https://hh-io.github.io/lol-esports-calendar/dist/ko/lpl.ics` |
| LCK (한국) | `https://hh-io.github.io/lol-esports-calendar/dist/ko/lck.ics` |
| LEC (유럽) | `https://hh-io.github.io/lol-esports-calendar/dist/ko/lec.ics` |
| LCP (태평양) | `https://hh-io.github.io/lol-esports-calendar/dist/ko/lcp.ics` |
| LTA (아메리카) | `https://hh-io.github.io/lol-esports-calendar/dist/ko/lta.ics` |
| 국제 대회 (MSI/Worlds/First Stand) | `https://hh-io.github.io/lol-esports-calendar/dist/ko/intl.ics` |

> 직접 포크해서 배포할 때는 `hh-io` / `lol-esports-calendar`를 본인 사용자명 / 저장소명으로 바꾸세요.

> 경기 시간은 UTC로 저장되며 Apple 캘린더가 자동으로 현지 시간대로 표시합니다.

## Apple 캘린더 구독 방법

**macOS**: 캘린더 앱 → 메뉴 **파일** → **새로운 캘린더 구독…** → URL 붙여넣기 → "자동 새로 고침"을 "매시간" 또는 "매일"로 설정.

**iPhone/iPad**: 설정 → 캘린더 → 계정 → 계정 추가 → 기타 → 구독 캘린더 추가 → URL 붙여넣기.

URL의 `https://`를 `webcal://`로 바꾸면 링크를 눌러 바로 캘린더 앱을 열 수 있습니다.

## Google 캘린더 / Outlook

같은 `.ics` URL을 다른 클라이언트에서도 구독할 수 있습니다:

- **Google 캘린더**(웹): "다른 캘린더" → "+" → "URL로 추가" → URL 붙여넣기.
- **Outlook**: "캘린더 추가" → "웹에서 구독" → URL 붙여넣기.

## 로컬 실행

```bash
python3 src/main.py      # dist/*.ics 및 dist/en, dist/ko 다국어 버전 생성
```

## 배포

1. 이 저장소를 GitHub에 푸시합니다.
2. **Settings → Pages**: Source를 `Deploy from a branch`, 브랜치 `main`, 폴더 `/ (root)`로 설정. 구독 경로는 `https://<user>.github.io/<repo>/dist/lpl.ics`입니다.
3. **Settings → Actions → General**: 워크플로에 `Read and write permissions`가 있는지 확인합니다.
4. **Actions** 탭에서 `Update LoL calendars` → `Run workflow`를 한 번 실행해 생성·커밋되는지 확인합니다. 이후 매시간 자동 갱신됩니다(경기 종료 후 약 1~2시간 내 점수 표시).

## 구조

```
src/fetch.py   getLeagues로 리그 ID 확인, getSchedule 페이지네이션, 이벤트 정규화(hl로 언어 제어)
src/ics.py     이벤트 → RFC 5545 .ics 텍스트(안정적 UID, CRLF, 75바이트 폴딩, 다국어 정적 문구)
src/main.py    언어 × 구독 그룹별 .ics 출력; 수집 실패 시 기존 파일 유지
.github/workflows/update.yml   예약 + 수동 트리거, 변경이 있을 때만 커밋
dist/          중국어 .ics; dist/en, dist/ko는 영어 / 한국어(Pages에서 호스팅)
```

## 데이터 출처 및 리스크

데이터는 lolesports.com이 자체적으로 사용하는 비공식 엔드포인트(`esports-api.lolesports.com/persisted/gw`, 고정 공개 `x-api-key` — 비밀 아님)에서 가져옵니다. 비공식이므로 Riot이 언제든 변경할 수 있습니다. 스크립트는 다음과 같이 방어적으로 동작합니다:

- `leagueId`는 매 실행마다 `getLeagues`에서 동적으로 확인합니다(slug 매칭, 하드코딩 안 함).
- 네트워크/API 실패 시 종료하고 **이전 `.ics`를 유지**하여 빈 파일로 구독을 덮어쓰지 않습니다.
- 비시즌에 예정 경기가 없는 지역은 빈 캘린더가 됩니다(정상 — 새 일정이 공개되면 자동으로 나타납니다).

`src/main.py`의 `OUTPUTS`에서 지역을, `LANGS`에서 언어를 추가/삭제할 수 있습니다(slug는 `getLeagues` 참고).
