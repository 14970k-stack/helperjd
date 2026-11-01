# 지수행정사 SNS 영상 제작

Azure Speech 음성, 한글 자막, 직접 합성한 배경음악을 포함하는 시험 영상을 GitHub Actions에서 생성합니다.

- 실행 파일: `.github/workflows/jisu-video.yml`
- 필요한 Repository secrets: `AZURE_SPEECH_KEY`, `AZURE_SPEECH_REGION`
- 결과: Actions 실행의 `jisu-voice-video-sample` artifact
- 확인 상태: 시험 영상 생성 성공. 매일 새 콘텐츠 전달과 Metricool 예약 발행 연결은 아직 미구현입니다.

목표 발행 시각: Asia/Seoul 오전 06:30 영상, 오후 15:30 이미지 글.
Threads의 상세 페이지 링크는 첫 답글로 게시합니다.

키와 토큰은 코드에 넣지 않습니다.
