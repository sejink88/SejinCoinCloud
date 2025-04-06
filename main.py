import streamlit as st
import pandas as pd
import ast
from datetime import datetime, timedelta, timezone
import random
import time
import gspread
from google.oauth2.service_account import Credentials
import os
import pickle

# --- Google Sheets API 연결 ---
def connect_gsheet():
    creds = Credentials.from_service_account_info(
        st.secrets["Drive"],
        scopes=["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    )
    client = gspread.authorize(creds)
    sheet_url = st.secrets["general"]["spreadsheet"]
    sheet = client.open_by_url(sheet_url).sheet1
    return sheet

# 캐시된 데이터를 로드하는 함수
def load_data_from_cache():
    cache_file = "data_cache.pkl"
    if os.path.exists(cache_file):
        with open(cache_file, "rb") as f:
            return pickle.load(f)
    else:
        return None

# 캐시된 데이터를 저장하는 함수
def save_data_to_cache(data):
    with open("data_cache.pkl", "wb") as f:
        pickle.dump(data, f)

# Google Sheets 데이터 로드
def load_data():
    cached_data = load_data_from_cache()
    if cached_data is not None:
        return cached_data
    else:
        sheet = connect_gsheet()
        data = pd.DataFrame(sheet.get_all_records())
        save_data_to_cache(data)
        return data

def save_data(data):
    sheet = connect_gsheet()
    sheet.update([data.columns.values.tolist()] + data.values.tolist())
    save_data_to_cache(data)

# 기록을 추가하는 함수 (KST 적용)
def add_record(student_index, activity, reward=None, additional_info=None):
    kst = timezone(timedelta(hours=9))
    timestamp = datetime.now(kst).strftime("%Y-%m-%d %H:%M:%S")
    record_list = ast.literal_eval(data.at[student_index, "기록"])
    new_record = {
        "timestamp": timestamp,
        "activity": activity,
        "reward": reward,
        "additional_info": additional_info
    }
    record_list.append(new_record)
    data.at[student_index, "기록"] = str(record_list)

# --- 로또 티켓 정보를 저장하는 함수 ---
def load_lotto_entries():
    filename = "lotto_entries.pkl"
    if os.path.exists(filename):
        with open(filename, "rb") as f:
            entries = pickle.load(f)
    else:
        entries = {}  # key: 반 이름, value: 로또 티켓 목록 (각 티켓은 dict)
    return entries

def save_lotto_entries(entries):
    with open("lotto_entries.pkl", "wb") as f:
        pickle.dump(entries, f)

# --- BGM 재생 함수 (동일 파일 사용) ---
def render_bgm():
    return st.audio("bgm.mp3", format="audio/mp3")

# --- 🌟 UI 스타일 ---
st.markdown(
    """
    <style>
    .stApp {
        background: url('https://i.ibb.co/vCZs9W58/bgi2.jpg') no-repeat center center fixed !important;
        background-size: cover !important;
    }
    .content-container {
        background-color: rgba(0, 0, 0, 0.7);
        padding: 20px;
        border-radius: 10px;
        max-width: 800px;
        margin: auto;
        font-size: 1.2em;
    }
    .header-img {
        width: 100%;
        max-height: 300px;
        object-fit: cover;
        border-radius: 10px;
        margin-bottom: 20px;
    }
    p, h1, h2, h3, h4, h5, h6 {
        background-color: rgba(0, 0, 0, 0.7);
        padding: 4px;
    }
    html, body, [class*="css"] {
        color: #ffffff;
        font-family: 'Orbitron', sans-serif;
    }
    .stButton>button {
        background-color: #808080 !important;
        color: #fff;
        font-weight: bold;
        border: none;
        border-radius: 8px;
        padding: 10px 20px;
        font-size: 16px;
        transition: transform 0.2s ease-in-out;
        box-shadow: 0px 4px 6px rgba(0,0,0,0.3);
    }
    /* 공 버튼 스타일 */
    div.ball-button > button {
        border-radius: 50%;
        width: 50px;
        height: 50px;
        font-size: 16px;
        margin: 5px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# 헤더 이미지 및 제목
st.markdown(
    '<div style="text-align:center;">'
    '<img class="header-img" src="https://media1.giphy.com/media/v1.Y2lkPTc5MGI3NjExemVldTNsMGVpMjZzdjhzc3hnbzl0d2szYjNoNXY2ZGt4ZXVtNncyciZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/30VBSGB7QW1RJpNcHO/giphy.gif" alt="Bitcoin GIF">'
    '</div>',
    unsafe_allow_html=True
)
st.markdown('<h1 style="text-align:center; font-size:3em; color:yellow; background-color:rgba(0,0,0,0.7); padding:10px; border-radius:10px;">$$세진코인$$</h1>', unsafe_allow_html=True)
st.markdown('<div class="content-container">', unsafe_allow_html=True)

# --- 🎓 UI 선택 ---
user_type = st.sidebar.radio("모드를 선택하세요", ["학생용", "교사용", "통계용", "로그 확인"])
data = load_data()

# (기타 교사용, 로그 확인, 통계용 UI는 생략하고 학생용 UI를 아래에 업데이트함)

# --- 학생용 UI ---
if user_type == "학생용":
    selected_class = st.selectbox("반을 선택하세요:", data["반"].unique())
    filtered_data = data[data["반"] == selected_class]
    selected_student = st.selectbox("학생을 선택하세요:", filtered_data["학생"].tolist())
    student_index = data[(data["반"] == selected_class) & (data["학생"] == selected_student)].index[0]
    student_coins = float(data.at[student_index, "세진코인"])
    st.markdown(
        f"<h2 style='background-color: rgba(0, 0, 0, 0.7); padding: 10px; border-radius: 8px;'>"
        f"{selected_student}님의 세진코인은 {student_coins:.1f}개입니다."
        f"</h2>",
        unsafe_allow_html=True
    )

    password = st.text_input("비밀번호를 입력하세요:", type="password")
    if password == str(data.at[student_index, "비밀번호"]):
        # 학생 비밀번호 입력 시 BGM 재생
        render_bgm()
        st.markdown(
            "<h2 style='background-color: rgba(0, 0, 0, 0.7); padding: 10px; border-radius: 8px;'>"
            "🎟 로또 티켓 구매 (1코인 차감)"
            "</h2>",
            unsafe_allow_html=True
        )
        # 공 모양의 버튼 인터페이스를 위한 초기화
        if "chosen_numbers" not in st.session_state:
            st.session_state["chosen_numbers"] = []
        st.markdown("**공을 클릭하여 숫자를 선택하세요 (최대 3개):**")
        # 20개의 공을 5개씩 4행으로 배치
        for row in range(4):
            cols = st.columns(5)
            for col_idx in range(5):
                number = row * 5 + col_idx + 1
                # 이미 선택된 숫자는 체크표시를 붙임
                if number in st.session_state["chosen_numbers"]:
                    button_label = f"✅ {number}"
                else:
                    button_label = str(number)
                if cols[col_idx].button(button_label, key=f"ball_{number}", help=f"{number}번 공"):
                    # 클릭하면 선택이 토글되도록 함 (최대 3개 제한)
                    if number in st.session_state["chosen_numbers"]:
                        st.session_state["chosen_numbers"].remove(number)
                    else:
                        if len(st.session_state["chosen_numbers"]) < 3:
                            st.session_state["chosen_numbers"].append(number)
        st.markdown(f"선택한 번호: {', '.join(map(str, st.session_state['chosen_numbers']))}")
        
        # 로또 티켓 구매 버튼: 선택한 숫자가 3개일 때만 구매 진행
        if len(st.session_state["chosen_numbers"]) == 3:
            if st.button("로또 티켓 구매"):
                # 동일한 번호 조합으로 이미 구매한 티켓이 있는지 확인
                entries = load_lotto_entries()
                class_name = selected_class
                duplicate_ticket = False
                if class_name in entries:
                    for ticket in entries[class_name]:
                        if (ticket["student_index"] == student_index and 
                            sorted(ticket["chosen_numbers"]) == sorted(st.session_state["chosen_numbers"])):
                            duplicate_ticket = True
                            break
                if duplicate_ticket:
                    st.error("동일한 번호로는 한 회차에 한 개만 구매 가능합니다.")
                else:
                    current_coins = float(data.at[student_index, "세진코인"])
                    if current_coins < 1:
                        st.error("세진코인이 부족하여 티켓 구매가 불가능합니다.")
                    else:
                        data.at[student_index, "세진코인"] = current_coins - 1
                        save_data(data)
                        if class_name not in entries:
                            entries[class_name] = []
                        ticket = {
                            "student_index": student_index,
                            "학생": selected_student,
                            "chosen_numbers": st.session_state["chosen_numbers"],
                            "timestamp": datetime.now(timezone(timedelta(hours=9))).strftime("%Y-%m-%d %H:%M:%S")
                        }
                        entries[class_name].append(ticket)
                        save_lotto_entries(entries)
                        add_record(student_index, "로또 티켓 구매", reward=None, additional_info=f"선택 번호: {st.session_state['chosen_numbers']}")
                        save_data(data)
                        st.success("티켓 구매 완료! 추첨은 관리자가 진행합니다.")
        else:
            st.info("숫자 1부터 20까지의 공 중 3개를 선택해야 티켓 구매가 가능합니다.")
        student_coins = float(data.at[student_index, "세진코인"])
        st.sidebar.markdown("---")
        st.sidebar.subheader("📌 학생 정보")
        st.sidebar.write(f"**이름:** {selected_student}")
        st.sidebar.write(f"**보유 코인:** {student_coins:.1f}개")
        st.sidebar.markdown("---")
        
# (교사용 및 통계용 UI는 기존 코드와 동일)
st.markdown('</div>', unsafe_allow_html=True)
