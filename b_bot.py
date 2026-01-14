import streamlit as st
import requests
from gtts import gTTS
import speech_recognition as sr
import os
import tempfile
from datetime import datetime
import base64
import time

st.set_page_config(page_title="제미나이 음성 비서", page_icon="🎙️", layout="wide")

st.markdown("""
<style>
    .main { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); }
    .stButton>button {
        width: 100%; height: 60px; font-size: 18px; font-weight: bold;
        border-radius: 15px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white; border: none; box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
        transition: all 0.3s;
    }
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(0, 0, 0, 0.3);
    }
    h1, h2, h3 { color: white; text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.2); }
    .response-box {
        background: white;
        border-radius: 15px;
        padding: 25px;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
        margin: 15px 0;
        line-height: 1.8;
        font-size: 16px;
    }
</style>
""", unsafe_allow_html=True)

if 'history' not in st.session_state:
    st.session_state.history = []
if 'api_key' not in st.session_state:
    st.session_state.api_key = ''
if 'response' not in st.session_state:
    st.session_state.response = ''
if 'transcript' not in st.session_state:
    st.session_state.transcript = ''
if 'last_request_time' not in st.session_state:
    st.session_state.last_request_time = 0

def recognize_speech():
    """음성 인식 함수"""
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        st.info("🎤 듣고 있습니다... 말씀해주세요!")
        try:
            recognizer.adjust_for_ambient_noise(source, duration=0.5)
            audio = recognizer.listen(source, timeout=5, phrase_time_limit=10)
            st.success("✅ 음성 수신 완료! 변환 중...")
            text = recognizer.recognize_google(audio, language='ko-KR')
            return text
        except sr.WaitTimeoutError:
            st.error("⏱️ 시간 초과: 음성이 감지되지 않았습니다.")
            return None
        except sr.UnknownValueError:
            st.error("❌ 음성을 인식할 수 없습니다. 다시 시도해주세요.")
            return None
        except sr.RequestError as e:
            st.error(f"❌ 음성 인식 서비스 오류: {e}")
            return None
        except Exception as e:
            st.error(f"❌ 오류 발생: {str(e)}")
            return None

def get_gemini_response(prompt, api_key):
    """Gemini 2.0 API 호출 (한국어 강제 + 요청 제한 체크)"""
    
    # 한국어로 답변하도록 프롬프트 수정
    korean_prompt = f"다음 질문에 한국어로 자세하고 친절하게 답변해주세요:\n\n{prompt}"
    
    # 요청 제한 방지 (4초 대기)
    current_time = time.time()
    time_since_last = current_time - st.session_state.last_request_time
    
    if time_since_last < 4:
        wait_time = 4 - time_since_last
        st.info(f"⏳ API 제한 방지를 위해 {wait_time:.1f}초 대기 중...")
        time.sleep(wait_time)
    
    try:
        # Gemini 2.0 Flash 모델 고정
        model_name = "gemini-2.0-flash-exp"
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"
        headers = {'Content-Type': 'application/json'}
        data = {"contents": [{"parts": [{"text": korean_prompt}]}]}
        
        response = requests.post(url, headers=headers, json=data, timeout=30)
        st.session_state.last_request_time = time.time()
        
        if response.status_code == 200:
            result = response.json()
            if 'candidates' in result and len(result['candidates']) > 0:
                return result['candidates'][0]['content']['parts'][0]['text']
            else:
                return "응답을 생성할 수 없습니다."
        
        elif response.status_code == 429:
            return "⚠️ **요청 한도 초과**\n\n무료 API는 분당 15회, 일일 1,500회로 제한됩니다.\n\n**해결 방법:**\n1. 1-2분 후 다시 시도\n2. 새 API 키 발급\n3. 내일 다시 시도"
        
        elif response.status_code == 400:
            error_data = response.json()
            error_msg = error_data.get('error', {}).get('message', '')
            return f"⚠️ **API 오류**\n\n{error_msg}\n\nAPI 키를 확인해주세요."
        
        elif response.status_code == 403:
            return "⚠️ **API 키 권한 오류**\n\nAPI 키를 다시 확인하거나 새로 발급받아주세요."
        
        else:
            error_data = response.json()
            error_msg = error_data.get('error', {}).get('message', '알 수 없는 오류')
            return f"⚠️ **API 오류 ({response.status_code})**\n\n{error_msg}"
            
    except requests.exceptions.Timeout:
        return "⚠️ 요청 시간 초과. 다시 시도해주세요."
    except requests.exceptions.ConnectionError:
        return "⚠️ 인터넷 연결을 확인해주세요."
    except Exception as e:
        return f"⚠️ 오류 발생: {str(e)}"

def text_to_speech(text):
    """TTS 함수"""
    try:
        # 경고 메시지는 음성 출력 안함
        if text.startswith("⚠️"):
            return None
            
        if len(text) > 500:
            text = text[:500] + "..."
        tts = gTTS(text=text, lang='ko')
        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as fp:
            tts.save(fp.name)
            return fp.name
    except Exception as e:
        st.error(f"TTS 오류: {str(e)}")
        return None

def autoplay_audio(file_path):
    """자동 오디오 재생"""
    try:
        with open(file_path, "rb") as f:
            data = f.read()
            b64 = base64.b64encode(data).decode()
            st.markdown(
                f'<audio autoplay="true"><source src="data:audio/mp3;base64,{b64}" type="audio/mp3"></audio>', 
                unsafe_allow_html=True
            )
        os.remove(file_path)
    except Exception as e:
        st.error(f"오디오 재생 오류: {str(e)}")

# 헤더
st.markdown("<h1 style='text-align: center; font-size: 48px;'>🎙️ 제미나이 음성 비서 프로그램</h1>", unsafe_allow_html=True)
st.markdown("<h3 style='text-align: center;'>AI 기반 대화형 어시스턴트</h3>", unsafe_allow_html=True)

with st.sidebar:
    st.header("⚙️ 설정")
    st.info("🔑 API 키 인증: https://aistudio.google.com/app/apikey")
    
    api_key = st.text_input(
        "Gemini API 키",
        type="password",
        value=st.session_state.api_key,
        placeholder="AIza로 시작하는 키를 입력하세요"
    )
    if api_key:
        st.session_state.api_key = api_key
        if api_key.startswith('AIza'):
            st.success("✅ API 키가 올바른 형식입니다")
        else:
            st.warning("⚠️ API 키는 보통 'AIza'로 시작합니다")
    
    st.markdown("---")
    
    st.subheader("🤖 모델 선택")
    st.write("사용할 수 있는 모델은 선택하세요")
    
    # Gemini 2.0 Flash만 고정으로 표시
    st.info("⚡ Gemini 2.0 Flash (실험적, 최신)")
    
    st.markdown("---")
    
    enable_tts = st.checkbox("🔊 음성(TTS)", value=True)
    
    st.markdown("---")
    
    # API 사용량 표시
    if st.session_state.history:
        st.metric("📊 이번 세션 요청 수", len(st.session_state.history))
        st.caption("무료 한도: 분당 15회, 일일 1,500회")
    
    st.markdown("---")
    
    with st.expander("ℹ️ 프로그램 정보", expanded=True):
        st.markdown("""
        **• STT:** 구글 음성 인식
        
        **• 답변:** Google Gemini AI
        
        **• TTS:** 구글 텍스트 음성 변환
        
        **• API:** REST API 직접 호출
        """)
    
    st.markdown("---")
    
    if st.button("🗑️ 대화 기록 초기화", use_container_width=True):
        st.session_state.history = []
        st.session_state.response = ''
        st.session_state.transcript = ''
        st.rerun()
    
    st.markdown("---")
    
    with st.expander("🛠️ 문제 해결"):
        st.markdown("""
        **요청 한도 초과:**
        - 1-2분 후 다시 시도
        - 새 API 키 발급
        
        **API 키 오류:**
        - API 키 재확인
        - 새 프로젝트에서 키 발급
        
        **음성 인식 안됨:**
        - 마이크 권한 확인
        - 조용한 환경에서 시도
        """)

# 메인 컨텐츠
col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("🎤 입력")
    
    if st.button("🎙️ 마이크로 질문하기", use_container_width=True, key="voice_btn"):
        if not st.session_state.api_key:
            st.error("⚠️ API 키를 먼저 입력해주세요!")
        else:
            text = recognize_speech()
            if text:
                st.session_state.transcript = text
                st.rerun()

with col2:
    st.subheader("⌨️ 입력")
    
    text_input = st.text_area(
        "",
        value=st.session_state.transcript,
        height=100,
        placeholder="예시:\n- 강아지를 영어로?\n- 파이썬 공부 방법 알려줘\n- 서울 맛집 추천해줘",
        label_visibility="collapsed"
    )
    
    if st.button("📤 질문 전송", use_container_width=True, type="primary"):
        if not st.session_state.api_key:
            st.error("⚠️ API 키를 먼저 입력해주세요!")
        elif not text_input:
            st.warning("⚠️ 질문을 입력해주세요!")
        else:
            st.session_state.transcript = text_input

# 질문 처리
if st.session_state.transcript and st.session_state.api_key:
    with st.spinner("🤔 AI가 답변을 생성하고 있습니다..."):
        response = get_gemini_response(
            st.session_state.transcript,
            st.session_state.api_key
        )
        st.session_state.response = response
        
        st.session_state.history.append({
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'question': st.session_state.transcript,
            'answer': response,
            'model': 'gemini-2.0-flash-exp'
        })
        
        if enable_tts:
            audio_file = text_to_speech(response)
            if audio_file:
                autoplay_audio(audio_file)
        
        st.session_state.transcript = ''
        st.rerun()

# 답변 표시
if st.session_state.response:
    st.markdown("---")
    st.subheader("💬 AI 답변")
    
    if st.session_state.response.startswith("⚠️"):
        st.warning(st.session_state.response)
    else:
        st.markdown(f'<div class="response-box">{st.session_state.response}</div>', unsafe_allow_html=True)

# 대화 기록
if st.session_state.history:
    st.markdown("---")
    st.subheader("📜 대화 기록")
    
    for idx, item in enumerate(reversed(st.session_state.history)):
        with st.expander(f"⏰ {item['timestamp']} - {item['question'][:50]}..."):
            st.markdown(f"**🤖 모델:** `{item['model']}`")
            st.markdown(f"**❓ 질문:**")
            st.info(item['question'])
            st.markdown(f"**💡 답변:**")
            if item['answer'].startswith("⚠️"):
                st.warning(item['answer'])
            else:
                st.success(item['answer'])

st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: white; padding: 20px; font-size: 14px;'>"
    "Made with ❤️ using Streamlit & Google Gemini 2.0 API<br>"
    "<small>한국어 자동 답변 | 자동 요청 제한 방지</small>"
    "</div>",
    unsafe_allow_html=True
)



import sys
from streamlit.web import cli as stcli
from streamlit import runtime

if __name__ == "__main__":
    # Streamlit이 이미 실행 중인지 확인합니다.
    if not runtime.exists():
        # 실행 중이 아니라면, streamlit 명령어를 통해 다시 실행합니다.
        sys.argv = ["streamlit", "run", sys.argv[0]]
        sys.exit(stcli.main())
        
        