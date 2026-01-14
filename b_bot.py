import subprocess
import sys
import os

# 1. 필수 패키지 자동 설치 및 초기화
def initialize_app():
    packages = ["streamlit", "streamlit-mic-recorder", "google-generativeai", "gTTS"]
    for package in packages:
        try:
            import_name = package.replace("-", "_").lower()
            __import__(import_name)
        except ImportError:
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])

    if not hasattr(sys, '_streamlit_run_script') and os.environ.get("STREAMLIT_ALREADY_RUNNING") != "true":
        os.environ["STREAMLIT_ALREADY_RUNNING"] = "true"
        subprocess.run([sys.executable, "-m", "streamlit", "run", sys.argv[0]])
        sys.exit()

initialize_app()

# ---------------------------------------------------------
# 2. 라이브러리 임포트
# ---------------------------------------------------------
import streamlit as st
import streamlit.components.v1 as components
from streamlit_mic_recorder import mic_recorder
import google.generativeai as genai
from gtts import gTTS
import tempfile
from datetime import datetime
import base64

# ---------------------------------------------------------
# 3. 디자인 및 가독성 설정 (CSS)
# ---------------------------------------------------------
st.set_page_config(page_title="제미나이 음성 비서", page_icon="🎙️", layout="wide")

st.markdown("""
<style>
    .main { background-color: #f0f2f6; }
    .stButton>button { 
        width: 100%; border-radius: 12px; font-weight: bold; height: 50px; 
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; border: none; 
    }
    .chat-bubble { 
        background: white; border-radius: 18px; padding: 25px; margin-bottom: 20px; 
        box-shadow: 0 4px 12px rgba(0,0,0,0.05); border-left: 8px solid #667eea;
    }
    .user-q { font-size: 1.1rem; font-weight: 600; color: #333; margin-bottom: 10px; }
    .ai-a { font-size: 1.25rem; line-height: 1.6; color: #2c3e50; }
    .api-status { font-size: 0.9rem; font-weight: bold; margin-top: 5px; }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# 4. 실시간 마이크 볼륨 비주얼라이저 (축소형 복구)
# ---------------------------------------------------------
def audio_visualizer():
    visualizer_html = """
    <div style="background: #1e1e1e; padding: 5px; border-radius: 10px; border: 1px solid #333; margin-bottom: 10px;">
        <div style="color: #4CAF50; font-size: 10px; font-family: sans-serif; margin-bottom: 3px; text-align: center; font-weight: bold;">AUDIO INPUT ACTIVE</div>
        <canvas id="canvas" style="width: 100%; height: 25px;"></canvas>
    </div>
    <script>
    async function startVisualizer() {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            const audioContext = new (window.AudioContext || window.webkitAudioContext)();
            const analyser = audioContext.createAnalyser();
            const source = audioContext.createMediaStreamSource(stream);
            source.connect(analyser);
            analyser.fftSize = 64;
            const bufferLength = analyser.frequencyBinCount;
            const dataArray = new Uint8Array(bufferLength);
            const canvas = document.getElementById('canvas');
            const ctx = canvas.getContext('2d');
            function draw() {
                requestAnimationFrame(draw);
                analyser.getByteFrequencyData(dataArray);
                ctx.clearRect(0, 0, canvas.width, canvas.height);
                const barWidth = (canvas.width / bufferLength) * 2;
                let x = 0;
                for(let i = 0; i < bufferLength; i++) {
                    let barHeight = dataArray[i] / 5;
                    ctx.fillStyle = `rgb(102, 126, ${dataArray[i]+150})`;
                    ctx.fillRect(x, canvas.height - barHeight, barWidth, barHeight);
                    x += barWidth + 2;
                }
            }
            draw();
        } catch (err) { console.error("Mic error:", err); }
    }
    startVisualizer();
    </script>
    """
    components.html(visualizer_html, height=65)

# ---------------------------------------------------------
# 5. 세션 상태 관리
# ---------------------------------------------------------
if 'history' not in st.session_state: st.session_state.history = []
if 'api_key' not in st.session_state: st.session_state.api_key = ''
if 'last_processed_id' not in st.session_state: st.session_state.last_processed_id = None
if 'api_valid' not in st.session_state: st.session_state.api_valid = None

# ---------------------------------------------------------
# 6. 핵심 처리 로직 (오류 해결 및 검색 지원)
# ---------------------------------------------------------
def validate_api_key(api_key):
    try:
        genai.configure(api_key=api_key)
        genai.list_models()
        return True
    except:
        return False

def get_chat_response(api_key, text_input):
    try:
        genai.configure(api_key=api_key)
        # 400 오류 방지를 위해 동적인 도구 할당 시도
        try:
            model = genai.GenerativeModel(model_name="gemini-2.0-flash-exp", tools=[{"google_search": {}}])
            response = model.generate_content(text_input)
        except:
            model = genai.GenerativeModel("gemini-2.0-flash-exp")
            response = model.generate_content(text_input)
        return response.text
    except Exception as e:
        return f"⚠️ 답변 생성 오류: {str(e)}"

def process_voice_to_text(api_key, audio_bytes):
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-2.0-flash-exp")
        response = model.generate_content([{"mime_type": "audio/webm", "data": audio_bytes}, "음성을 텍스트로만 받아쓰기해줘."])
        return response.text.strip()
    except Exception as e:
        return f"인식 실패: {str(e)}"

def text_to_speech(text):
    try:
        clean_text = text.replace('*', '').replace('#', '')[:300]
        tts = gTTS(text=clean_text, lang='ko')
        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as fp:
            tts.save(fp.name)
            return fp.name
    except: return None

def autoplay_audio(file_path):
    with open(file_path, "rb") as f:
        data = f.read()
        b64 = base64.b64encode(data).decode()
        st.markdown(f'<audio autoplay="true"><source src="data:audio/mp3;base64,{b64}" type="audio/mp3"></audio>', unsafe_allow_html=True)
    os.remove(file_path)

# ---------------------------------------------------------
# 7. UI 레이아웃
# ---------------------------------------------------------
st.markdown("<h1 style='text-align: center; color: #4A90E2;'>🎙️ 제미나이 음성 비서</h1>", unsafe_allow_html=True)

with st.sidebar:
    st.header("⚙️ 설정")
    input_key = st.text_input("Gemini API 키 입력", type="password", value=st.session_state.api_key)
    
    if input_key and input_key != st.session_state.api_key:
        st.session_state.api_key = input_key
        st.session_state.api_valid = validate_api_key(input_key)
    
    # [복구] API 연결 정보 표시
    if st.session_state.api_key:
        if st.session_state.api_valid:
            st.markdown('<p style="color: #28a745;" class="api-status">✅ API 연결됨 (Gemini 2.0 Ready)</p>', unsafe_allow_html=True)
        else:
            st.markdown('<p style="color: #dc3545;" class="api-status">❌ 잘못된 API 키</p>', unsafe_allow_html=True)
            
    enable_tts = st.checkbox("🔊 음성 출력(TTS) 활성화", value=True)
    st.markdown("---")
    
    # [복구] 프로그램 정보 (줄바꿈 정렬)
    with st.expander("ℹ️ 프로그램 정보", expanded=True):
        st.write("**• STT:** 제미나이 격리 인식")
        st.write("**• 답변:** Google Gemini AI (검색 지원)")
        st.write("**• TTS:** 구글 텍스트 음성 변환")
        st.write("**• API:** Google AI SDK 사용")
    
    if st.button("🗑️ 기록 초기화", use_container_width=True):
        st.session_state.history = []; st.session_state.last_processed_id = None; st.rerun()

# ---------------------------------------------------------
# 8. 메인 인터랙티브 섹션   ---             
# ---------------------------------------------------------

import streamlit as st
from datetime import datetime


# 1. 스타일 설정 (공백 최소화 및 파란색 테마)
st.markdown("""
    <style>
    /* 버튼 스타일 (파란색) */
    div.stButton > button, 
    div.stForm submit_button > button {
        background-color: #007bff !important;
        color: white !important;
        border: 1px solid #007bff !important;
        width: 100% !important;
        height: 3em !important;
        border-radius: 8px !important;
        font-weight: bold !important;
    }
    
    /* 볼륨 비주얼라이저 (높이 살짝 조절) */
    .vol-container {
        display: flex;
        justify-content: center;
        align-items: center;
        height: 50px;
        background: #f0f7ff;
        border-radius: 8px;
        margin-bottom: 10px;
        border: 1px solid #cce5ff;
    }
    .vol-bar {
        width: 4px; height: 12px; background: #007bff;
        margin: 0 2px; border-radius: 5px;
        animation: wave 1s infinite ease-in-out;
    }
    @keyframes wave { 0%, 100% { height: 10px; opacity: 0.5; } 50% { height: 30px; opacity: 1; } }

    /* 폼 내부 여백 줄이기 */
    [data-testid="stForm"] {
        padding: 0px !important;
        border: none !important;
    }
    </style>
""", unsafe_allow_html=True)

# 2. 질문 처리 함수
def ask_ai_with_time(api_key, user_input):
    now_info = datetime.now().strftime("%Y년 %m월 %d일 %H시 %M분 %S초")
    enriched_prompt = f"현재 시각은 {now_info}입니다. 이 정보를 바탕으로 다음 질문에 답해주세요: {user_input}"
    return get_chat_response(api_key, enriched_prompt)

col1, col2 = st.columns(2)

# --- 🎤 음성 질문 섹션 (왼쪽) ---
with col1:
    st.subheader("🎤 음성 질문")
    with st.container(border=True):
        st.markdown('<div class="vol-container"><div class="vol-bar" style="animation-delay:0s"></div><div class="vol-bar" style="animation-delay:0.2s"></div><div class="vol-bar" style="animation-delay:0.4s"></div><div class="vol-bar" style="animation-delay:0.2s"></div><div class="vol-bar" style="animation-delay:0s"></div></div>', unsafe_allow_html=True)
        
        if st.session_state.get('api_valid', False):
            audio = mic_recorder(start_prompt="🔵 대화 시작", stop_prompt="🛑 분석 요청", key='recorder', use_container_width=True)
            if audio:
                current_id = audio.get('id')
                if current_id != st.session_state.get('last_processed_id'):
                    st.session_state.last_processed_id = current_id
                    with st.spinner("🎧 분석 중..."):
                        user_text = process_voice_to_text(st.session_state.api_key, audio['bytes'])
                        ai_a = ask_ai_with_time(st.session_state.api_key, user_text)
                        st.session_state.history.append({"q": f"🎙️ {user_text}", "a": ai_a, "time": datetime.now().strftime("%H:%M:%S")})
                    st.rerun()
        else:
            st.info("API 키를 입력하세요.")

# --- ⌨️ 텍스트 질문 섹션 (오른쪽) ---
with col2:
    st.subheader("⌨️ 텍스트 질문")
    with st.container(border=True):
        # 상단 공백을 70px에서 15px로 줄여서 위로 바짝 붙임
        st.markdown('<div style="height:15px;"></div>', unsafe_allow_html=True)
        
        with st.form(key='text_input_form', clear_on_submit=True):
            t_input = st.text_input(label="질문 내용", placeholder="궁금한 것을 물어보세요.", label_visibility="collapsed")
            submit_button = st.form_submit_button(label='📤 질문 전송', use_container_width=True)
            
            if submit_button and t_input and st.session_state.get('api_valid', False):
                with st.spinner("🤔 생각 중..."):
                    ai_a = ask_ai_with_time(st.session_state.api_key, t_input)
                    st.session_state.history.append({"q": t_input, "a": ai_a, "time": datetime.now().strftime("%H:%M:%S")})
                st.rerun()

# --- 채팅 이력 출력 ---
st.markdown("---")
if st.session_state.get('history'):
    for item in reversed(st.session_state.history):
        st.markdown(f"""
        <div style="border: 1px solid #e0e6ed; padding: 15px; border-radius: 10px; margin-bottom: 10px; background-color: #f8f9fa;">
            <div style="color: #888; font-size: 0.8rem; margin-bottom: 5px;">[{item['time']}]</div>
            <div style="font-weight: bold; color: #007bff;">Q: {item['q']}</div>
            <div style="margin-top: 5px;"><b>A:</b> {item['a']}</div>
        </div>
        """, unsafe_allow_html=True)