import subprocess
import sys
import os

# [수정] 재생 버튼 클릭 시 streamlit run 명령어로 자동 전환해주는 로직
if __name__ == "__main__":
    if not hasattr(sys, '_streamlit_run_script') and os.environ.get("STREAMLIT_ALREADY_RUNNING") != "true":
        os.environ["STREAMLIT_ALREADY_RUNNING"] = "true"
        # 현재 파일을 streamlit run으로 다시 실행합니다.
        subprocess.run([sys.executable, "-m", "streamlit", "run", sys.argv[0]])
        sys.exit()

# ---------------------------------------------------------
# 아래부터는 스트림릿 본 코드입니다.
# ---------------------------------------------------------
import streamlit as st
from streamlit_mic_recorder import mic_recorder
import google.generativeai as genai
from gtts import gTTS
import tempfile
from datetime import datetime
import base64


# 1. 페이지 설정 및 디자인 (최상단)
st.set_page_config(page_title="제미나이 음성 비서", page_icon="🎙️", layout="wide")

st.markdown("""
    <style>
    /* 전체 배경색 */
    .main { background-color: #f8f9fa; }
    
    /* 모든 버튼을 파란색으로 고정 및 빨간 테두리 제거 */
    div.stButton > button, div.stForm submit_button > button {
        background-color: #007bff !important;
        color: white !important;
        border: 1px solid #007bff !important;
        width: 100% !important;
        height: 3.5em !important;
        border-radius: 10px !important;
        font-weight: bold !important;
        box-shadow: none !important;
    }
    
    /* 입력창 포커스 시 파란색 테두리 */
    .stTextInput > div > div > input:focus {
        border-color: #007bff !important;
    }

    /* 볼륨 비주얼라이저 박스 */
    .vol-container {
        display: flex; justify-content: center; align-items: center; height: 50px;
        background: #f0f7ff; border-radius: 8px; margin-bottom: 10px; border: 1px solid #cce5ff;
    }
    .vol-bar {
        width: 4px; height: 12px; background: #007bff; margin: 0 2px; border-radius: 5px;
        animation: wave 1s infinite ease-in-out;
    }
    @keyframes wave { 0%, 100% { height: 10px; opacity: 0.5; } 50% { height: 30px; opacity: 1; } }

    /* 텍스트 질문 박스 내부 여백 최적화 */
    [data-testid="stForm"] { padding: 0px !important; border: none !important; }
    </style>
""", unsafe_allow_html=True)

# 2. 세션 상태 관리
if 'history' not in st.session_state: st.session_state.history = []
if 'api_key' not in st.session_state: st.session_state.api_key = ''
if 'last_processed_id' not in st.session_state: st.session_state.last_processed_id = None
if 'api_valid' not in st.session_state: st.session_state.api_valid = None

# 3. 핵심 로직 함수
def validate_api_key(api_key):
    try:
        genai.configure(api_key=api_key)
        genai.list_models()
        return True
    except: return False

def get_chat_response(api_key, text_input):
    """AI 응답을 가져오는 핵심 함수"""
    try:
        genai.configure(api_key=api_key)
        # 현재 시간(2026년) 정보를 주입하여 답변 정확도 향상
        now_info = datetime.now().strftime("%Y년 %m월 %d일 %H시 %M분 %S초")
        enriched_prompt = f"현재 시각은 {now_info}입니다. 이 시점을 기준으로 답변해주세요: {text_input}"
        
        model = genai.GenerativeModel("gemini-2.0-flash")
        response = model.generate_content(enriched_prompt)
        return response.text
    except Exception as e:
        return f"⚠️ 답변 생성 오류: {str(e)}"

def process_voice_to_text(api_key, audio_bytes):
    """음성을 텍스트로 변환 (STT)"""
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-2.0-flash")
        response = model.generate_content([
            {"mime_type": "audio/webm", "data": audio_bytes}, 
            "음성을 텍스트로만 정확히 받아쓰기해줘."
        ])
        return response.text.strip()
    except Exception as e:
        return f"인식 실패: {str(e)}"

def text_to_speech(text):
    """텍스트를 음성으로 변환 (TTS)"""
    try:
        clean_text = text.replace('*', '').replace('#', '')[:300]
        tts = gTTS(text=clean_text, lang='ko')
        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as fp:
            tts.save(fp.name)
            return fp.name
    except: return None

def autoplay_audio(file_path):
    """음성 자동 재생"""
    with open(file_path, "rb") as f:
        data = f.read()
        b64 = base64.b64encode(data).decode()
        st.markdown(f'<audio autoplay="true"><source src="data:audio/mp3;base64,{b64}" type="audio/mp3"></audio>', unsafe_allow_html=True)
    os.remove(file_path)

# 4. 화면 레이아웃
st.markdown("<h1 style='text-align: center; color: #007bff;'>🎙️ 제미나이 음성 비서</h1>", unsafe_allow_html=True)

with st.sidebar:
    st.header("⚙️ 설정")
    input_key = st.text_input("Gemini API 키 입력", type="password", value=st.session_state.api_key)
    
    if input_key and input_key != st.session_state.api_key:
        st.session_state.api_key = input_key
        st.session_state.api_valid = validate_api_key(input_key)
    
    if st.session_state.api_valid:
        st.success("✅ API 연결됨 (Gemini 2.0)")
    elif st.session_state.api_key:
        st.error("❌ 잘못된 API 키")
        
    enable_tts = st.checkbox("🔊 음성 출력(TTS) 활성화", value=True)
    st.markdown("---")

    # 프로그램 정보 섹션 복구
    with st.expander("ℹ️ 프로그램 정보", expanded=True):
        st.write("**• STT:** 제미나이 격리 인식")
        st.write("**• 답변:** Google Gemini AI (검색 지원)")
        st.write("**• TTS:** 구글 텍스트 음성 변환")
        st.write("**• API:** Google AI SDK 사용")    
    
    
    if st.button("🗑️ 기록 초기화", use_container_width=True):
        st.session_state.history = []; st.session_state.last_processed_id = None; st.rerun()

# 5. 메인 인터랙티브 섹션
col1, col2 = st.columns(2)

with col1:
    st.subheader("🎤 음성 질문")
    with st.container(border=True):
        # 볼륨 비주얼라이저
        st.markdown('<div class="vol-container"><div class="vol-bar" style="animation-delay:0s"></div><div class="vol-bar" style="animation-delay:0.2s"></div><div class="vol-bar" style="animation-delay:0.4s"></div><div class="vol-bar" style="animation-delay:0.2s"></div><div class="vol-bar" style="animation-delay:0s"></div></div>', unsafe_allow_html=True)
        
        if st.session_state.api_valid:
            audio = mic_recorder(start_prompt="🔵 대화 시작", stop_prompt="🛑 분석 요청", key='recorder', use_container_width=True)
            if audio:
                if audio.get('id') != st.session_state.last_processed_id:
                    st.session_state.last_processed_id = audio.get('id')
                    with st.spinner("🎧 분석 중..."):
                        user_text = process_voice_to_text(st.session_state.api_key, audio['bytes'])
                        ai_a = get_chat_response(st.session_state.api_key, user_text)
                        st.session_state.history.append({"q": f"🎙️ {user_text}", "a": ai_a, "time": datetime.now().strftime("%H:%M:%S")})
                        if enable_tts:
                            path = text_to_speech(ai_a)
                            if path: autoplay_audio(path)
                    st.rerun()
        else:
            st.info("API 키를 먼저 입력하세요.")

with col2:
    st.subheader("⌨️ 텍스트 질문")
    with st.container(border=True):
        # 상단 공백 최적화
        st.markdown('<div style="height:15px;"></div>', unsafe_allow_html=True)
        with st.form(key='text_input_form', clear_on_submit=True):
            t_input = st.text_input(label="질문 내용", placeholder="궁금한 것을 물어보세요.", label_visibility="collapsed")
            submit_button = st.form_submit_button(label='📤 질문 전송', use_container_width=True)
            
            if submit_button and t_input and st.session_state.api_valid:
                with st.spinner("🤔 생각 중..."):
                    ai_a = get_chat_response(st.session_state.api_key, t_input)
                    st.session_state.history.append({"q": t_input, "a": ai_a, "time": datetime.now().strftime("%H:%M:%S")})
                    if enable_tts:
                        path = text_to_speech(ai_a)
                        if path: autoplay_audio(path)
                st.rerun()

# 6. 채팅 이력 표시
st.markdown("---")
if st.session_state.history:
    for item in reversed(st.session_state.history):
        st.markdown(f"""
        <div style="border: 1px solid #e0e6ed; padding: 15px; border-radius: 10px; margin-bottom: 10px; background-color: #ffffff;">
            <div style="color: #888; font-size: 0.8rem; margin-bottom: 5px;">[{item['time']}]</div>
            <div style="font-weight: bold; color: #007bff;">Q: {item['q']}</div>
            <div style="margin-top: 5px;"><b>A:</b> {item['a']}</div>
        </div>

        """, unsafe_allow_html=True)
