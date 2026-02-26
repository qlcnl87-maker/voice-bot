# 🎙️ 제미나이 음성 비서 (Gemini Voice Bot)

Google Gemini AI를 활용한 음성 & 텍스트 기반 대화형 챗봇입니다.  
Streamlit으로 구현된 웹 인터페이스에서 음성 또는 텍스트로 질문하면 AI가 답변을 생성하고, TTS(텍스트 음성 변환)로 읽어줍니다.

🔗 **배포 주소**: [voice-bot-ywfpeao5tb8iifaajcjuuw.streamlit.app](https://voice-bot-ywfpeao5tb8iifaajcjuuw.streamlit.app/)

---

## ✨ 주요 기능

| 기능 | 설명 |
|------|------|
| 🎤 음성 질문 (STT) | 마이크로 말하면 텍스트로 변환하여 AI에 전달 |
| ⌨️ 텍스트 질문 | 직접 텍스트를 입력하여 AI에 질문 |
| 🤖 AI 답변 생성 | Google Gemini AI가 답변 생성 (웹 검색 지원) |
| 🔊 음성 출력 (TTS) | 구글 텍스트 음성 변환으로 답변을 음성으로 출력 |
| 📋 대화 기록 | 이전 질문/답변 내역 확인 및 초기화 |

---

## 🛠️ 기술 스택

- **Frontend / UI**: Streamlit
- **AI 모델**: Google Gemini API (`gemini-2.0-flash`)
- **음성 인식 (STT)**: Google Gemini 격리 인식
- **음성 출력 (TTS)**: 구글 텍스트 음성 변환 (gTTS)
- **언어**: Python

---

## 📁 프로젝트 구조

```
voice-bot/
├── b_bot.py            # 메인 애플리케이션
├── requirements.txt    # Python 패키지 목록
├── packages.txt        # 시스템 패키지 목록
└── .devcontainer/      # 개발 컨테이너 설정
```

---

## 🚀 로컬 실행 방법

### 1. 레포지토리 클론

```bash
git clone https://github.com/qlcnl87-maker/voice-bot.git
cd voice-bot
```

### 2. 패키지 설치

```bash
pip install -r requirements.txt
```

### 3. 앱 실행

```bash
streamlit run b_bot.py
```

### 4. 브라우저에서 접속

```
http://localhost:8501
```

---

## 🔑 API 키 설정

1. [Google AI Studio](https://aistudio.google.com/app/apikey)에서 Gemini API 키 발급
2. 앱 실행 후 왼쪽 사이드바 **"Gemini API 키 입력"** 란에 키 입력
3. ✅ API 연결됨 표시 확인 후 사용

---

## 💡 사용 방법

### 텍스트 질문
1. 오른쪽 **"텍스트 질문"** 영역에 질문 입력
2. **"질문 전송"** 버튼 클릭
3. 하단 대화 기록에서 답변 확인

### 음성 질문
1. 왼쪽 **"음성 질문"** 영역에서 **"대화 시작"** 클릭
2. 마이크에 질문 말하기
3. 자동으로 인식 후 AI가 답변 생성

### 음성 출력 설정
- 사이드바에서 **"음성 출력(TTS) 활성화"** 체크박스로 ON/OFF 조절

---

## ⚠️ 주의사항

- Gemini API 키가 없으면 동작하지 않습니다
- 음성 기능 사용 시 마이크 권한을 허용해야 합니다
- 무료 API 키는 분당 요청 횟수 제한이 있습니다

---

## 📝 개발자

- **GitHub**: [@qlcnl87-maker](https://github.com/qlcnl87-maker)
