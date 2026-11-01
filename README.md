# 지수행정사 SNS 자동 제작

## 현재 제작 경로
1. ChatGPT 자동 작업은 Asia/Seoul 오전 05:00 시작.
2. 새로운 9:16 만화 6장면을 2열 3행 atlas로 생성. 각 장면은 9:16이며 고정 캐릭터·가상 사례로 구성.
3. atlas JPEG bytes를 base64로 인코딩해 assets/storyboard.b64에 저장. 원본 이미지를 수정하지 않고 영상 장면을 구성하기 위한 운반 형식.
4. content/current.json의 batch_id·title·detail_url·scenes(heading/title/narration)를 해당 원고로 갱신. assets 먼저, content 마지막 커밋 권장. push마다 렌더가 실행되므로 원고 최종 commit SHA와 일치하는 run만 사용.
5. GitHub Actions가 render.py를 실행하고 Repository Secrets의 Azure 키를 사용해 한국어 음성을 생성. 원본 합성 BGM을 작게 깔고 음성 동안 자동 감쇄.
6. 동일 commit SHA의 workflow run 완료를 확인하고 artifact를 가져와 MP4 프레임·음성·길이 검증.
7. Metricool로 오전 06:30 영상, 오후 15:30 별도 이미지 게시물 등록. 댓글/첫 답글에 주제별 정상 접근 가능한 상세 URL을 넣고 게시 상태 확인.

## Secret
AZURE_SPEECH_KEY, AZURE_SPEECH_REGION. 키를 출력·복사·원고에 포함하지 않음.

## 게시 채널
Facebook 페이지 434527969745416 / Instagram 및 Threads helperjd611 / Metricool brandId 7790650.
YouTube는 연결된 ID만 확인됐고 채널 분야가 아직 확인되지 않아 게시 대상에 포함하지 않음.

## 상태 구분
영상 제작은 GitHub Actions, SNS 발행은 ChatGPT의 Metricool 연결이 담당. GitHub 워크플로 자체에 Metricool 자격증명이나 직접 발행 코드는 없음. ChatGPT 예약이 끝까지 실행하고 상태를 검증해야 완전한 발행 결과로 보고할 수 있음. 실패시 중복 게시하지 말 것.
