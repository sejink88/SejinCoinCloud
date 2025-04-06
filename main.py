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

# 캐시된 데이터를 로드/저장하는 함수들
def load_data_from_cache():
    cache_file = "data_cache.pkl"
    if os.path.exists(cache_file):
        with open(cache_file, "rb") as f:
            return pickle.load(f)
    else:
        return None

def save_data_to_cache(data):
    with open("data_cache.pkl", "wb") as f:
        pickle.dump(data, f)

# Google Sheets 데이터 로드 및 저장
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

# --- BGM 재생 함수 ---
def render_bgm():
    st.audio("bgm.mp3", format="audio/mp3")

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

# --- 모드 선택 ---
user_type = st.sidebar.radio("모드를 선택하세요", ["학생용", "교사용", "통계용", "로그 확인"])
data = load_data()

# ================================
# 교사용 모드
# ================================
if user_type == "교사용":
    st.header("교사용 모드")
    selected_class = st.selectbox("반을 선택하세요:", data["반"].unique())
    filtered_data = data[data["반"] == selected_class]
    selected_student = st.selectbox("학생을 선택하세요:", filtered_data["학생"].tolist())
    student_index = data[(data["반"] == selected_class) & (data["학생"] == selected_student)].index[0]
    password = st.text_input("관리자 비밀번호를 입력하세요:", type="password")
    if password == st.secrets["general"]["admin_password"]:
        render_bgm()  # 관리자 BGM 재생
        # 개별 학생 코인 부여/차감 및 비밀번호 변경
        coin_amount = st.number_input("부여 또는 회수할 코인 수:", min_value=-100, max_value=100, value=1)
        if st.button("세진코인 변경하기"):
            if coin_amount != 0:
                data.at[student_index, "세진코인"] += coin_amount
                add_record(student_index, "세진코인 변경", reward=None, additional_info=f"변경된 코인: {coin_amount}")
                save_data(data)
                if coin_amount > 0:
                    st.success(f"{selected_student}에게 세진코인 {coin_amount}개를 부여했습니다!")
                else:
                    st.warning(f"{selected_student}에게서 세진코인 {-coin_amount}개를 회수했습니다!")
        st.subheader("비밀번호 변경")
        new_password = st.text_input("새로운 비밀번호 입력:", type="password")
        if st.button("비밀번호 변경"):
            data.at[student_index, "비밀번호"] = new_password
            save_data(data)
            st.success(f"{selected_student}의 비밀번호가 성공적으로 변경되었습니다!")
        if st.button("⚠️ 세진코인 초기화"):
            data.at[student_index, "세진코인"] = 0
            data.at[student_index, "기록"] = "[]"
            add_record(student_index, "세진코인 초기화", reward=None, additional_info="세진코인 및 기록 초기화")
            save_data(data)
            st.error(f"{selected_student}의 세진코인이 초기화되었습니다!")

        # 학급 전체 일괄 작업
        st.markdown("---")
        st.subheader("학급 전체 일괄 작업")
        batch_coin_amount = st.number_input("전체 학급에 부여/차감할 코인 수:", min_value=-100, max_value=100, value=1, key="batch_coin")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("전체 일괄 부여/차감", key="batch_change"):
                class_indices = data[data["반"] == selected_class].index
                for idx in class_indices:
                    data.at[idx, "세진코인"] += batch_coin_amount
                    add_record(idx, "학급 전체 세진코인 변경", reward=None, additional_info=f"일괄 변경된 코인: {batch_coin_amount}")
                save_data(data)
                if batch_coin_amount > 0:
                    st.success(f"{selected_class} 전체 학생에게 세진코인 {batch_coin_amount}개 부여 완료!")
                else:
                    st.warning(f"{selected_class} 전체 학생에게서 세진코인 {-batch_coin_amount}개 회수 완료!")
        with col2:
            if st.button("전체 세진코인 초기화", key="batch_reset"):
                class_indices = data[data["반"] == selected_class].index
                for idx in class_indices:
                    data.at[idx, "세진코인"] = 0
                    data.at[idx, "기록"] = "[]"
                    add_record(idx, "학급 전체 세진코인 초기화", reward=None, additional_info="일괄 초기화")
                save_data(data)
                st.error(f"{selected_class} 전체 학생의 세진코인 초기화 완료!")
        
        # 반 단위 로또 추첨 (관리자 전용)
        st.markdown("---")
        st.subheader("반 단위 로또 추첨")
        if st.button("해당 반 로또 추첨 진행"):
            entries = load_lotto_entries()
            class_name = selected_class
            if class_name not in entries or len(entries[class_name]) == 0:
                st.warning("해당 반에 구매한 로또 티켓이 없습니다.")
            else:
                tickets = entries[class_name]
                st.info(f"{len(tickets)}개의 로또 티켓이 있습니다. 추첨을 진행합니다.")
                countdown_placeholder = st.empty()
                loading_image = "https://media3.giphy.com/media/v1.Y2lkPTc5MGI3NjExZjNmaDVzbTlrYWJrMXZzMGZkam5tOWc5OHQ5eDBhYm94OWxzN2hnZiZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/APqEbxBsVlkWSuFpth/giphy.gif"
                for i in range(7, 0, -1):
                    countdown_placeholder.markdown(f"**로또 추첨까지 {i}초 남음...**")
                    countdown_placeholder.image(loading_image, width=200)
                    time.sleep(1)
                countdown_placeholder.empty()
                pool = list(range(1, 21))
                main_balls = random.sample(pool, 3)
                main_ball_gif = "https://media2.giphy.com/media/v1.Y2lkPTc5MGI3NjExazYzZXp0azhvdjF1M3BtM3JobjVic2Y3ZWIyaTh4ZXpkNDNwdDZtdSZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/dvgefaMHmaN2g/giphy.gif"
                mapping = {1: "첫번째", 2: "두번째", 3: "세번째"}
                for idx, ball in enumerate(main_balls, start=1):
                    ball_placeholder = st.empty()
                    ball_placeholder.image(main_ball_gif, width=200)
                    time.sleep(3)
                    ball_placeholder.markdown(
                        f"<span style='font-size:300%; background-color:red; color:white;'>{mapping[idx]} 공: {ball}</span> :tada:",
                        unsafe_allow_html=True
                    )
                bonus_needed = any(len(set(ticket["chosen_numbers"]) & set(main_balls)) == 2 for ticket in tickets)
                bonus_ball = None
                if bonus_needed:
                    bonus_placeholder = st.empty()
                    for k in range(10, 0, -1):
                        bonus_placeholder.markdown(f"**보너스 공 추첨까지 {k}초 남음...**")
                        time.sleep(1)
                    bonus_placeholder.empty()
                    bonus_placeholder = st.empty()
                    bonus_placeholder.image(main_ball_gif, width=200)
                    time.sleep(3)
                    bonus_ball = random.choice([n for n in pool if n not in main_balls])
                    bonus_placeholder.markdown(
                        f"<span style='font-size:300%; background-color:red; color:white;'>보너스 공: {bonus_ball}</span> :sparkles:",
                        unsafe_allow_html=True
                    )
                winners = []
                for ticket in tickets:
                    ticket_numbers = ticket["chosen_numbers"]
                    student_idx = ticket["student_index"]
                    match_count = len(set(ticket_numbers) & set(main_balls))
                    reward = None
                    if match_count == 3:
                        reward = "치킨"
                    elif match_count == 2:
                        remaining_number = list(set(ticket_numbers) - set(main_balls))[0]
                        if bonus_ball is not None and remaining_number == bonus_ball:
                            reward = "햄버거세트"
                        else:
                            reward = "매점이용권"
                    elif match_count == 1:
                        reward = "0.5코인"
                        data.at[student_idx, "세진코인"] += 0.5
                    if reward:
                        add_record(student_idx, "로또 당첨", reward, f"당첨 번호: {main_balls}, 선택 번호: {ticket_numbers}")
                        winners.append({
                            "학생": ticket["학생"],
                            "당첨 보상": reward,
                            "선택 번호": ticket_numbers,
                            "당첨 번호": main_balls
                        })
                save_data(data)
                entries[class_name] = []
                save_lotto_entries(entries)
                if winners:
                    st.success("로또 당첨 결과:")
                    st.table(pd.DataFrame(winners))
                else:
                    st.info("아쉽게도 당첨된 티켓이 없습니다.")
    else:
        st.error("관리자 비밀번호를 입력하세요.")

# ================================
# 학생용 모드
# ================================
elif user_type == "학생용":
    st.header("학생용 모드")
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
        render_bgm()
        st.markdown(
            "<h2 style='background-color: rgba(0, 0, 0, 0.7); padding: 10px; border-radius: 8px;'>"
            "🎟 로또 티켓 구매 (1코인 차감)"
            "</h2>",
            unsafe_allow_html=True
        )
        # 공 모양의 버튼 인터페이스
        if "chosen_numbers" not in st.session_state:
            st.session_state["chosen_numbers"] = []
        st.markdown("**공을 클릭하여 숫자를 선택하세요 (최대 3개):**")
        for row in range(4):
            cols = st.columns(5)
            for col_idx in range(5):
                number = row * 5 + col_idx + 1
                if number in st.session_state["chosen_numbers"]:
                    button_label = f"✅ {number}"
                else:
                    button_label = str(number)
                if cols[col_idx].button(button_label, key=f"ball_{number}"):
                    if number in st.session_state["chosen_numbers"]:
                        st.session_state["chosen_numbers"].remove(number)
                    else:
                        if len(st.session_state["chosen_numbers"]) < 3:
                            st.session_state["chosen_numbers"].append(number)
        st.markdown(f"선택한 번호: {', '.join(map(str, st.session_state['chosen_numbers']))}")
        if len(st.session_state["chosen_numbers"]) == 3:
            if st.button("로또 티켓 구매"):
                entries = load_lotto_entries()
                class_name = selected_class
                duplicate_ticket = False
                if class_name in entries:
                    for ticket in entries[class_name]:
                        if ticket["student_index"] == student_index and sorted(ticket["chosen_numbers"]) == sorted(st.session_state["chosen_numbers"]):
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

# ================================
# 로그 확인 모드
# ================================
elif user_type == "로그 확인":
    st.header("로그 확인 모드")
    selected_class_log = st.selectbox("반 선택:", data["반"].unique())
    filtered_data_log = data[data["반"] == selected_class_log]
    selected_student_log = st.selectbox("학생 선택:", filtered_data_log["학생"].tolist())
    student_index_log = data[(data["반"] == selected_class_log) & (data["학생"] == selected_student_log)].index[0]
    log_password = st.text_input("비밀번호 입력:", type="password")
    if log_password:
        admin_password = st.secrets["general"]["admin_password"]
        student_password = str(data.at[student_index_log, "비밀번호"])
        if log_password == admin_password or log_password == student_password:
            st.subheader(f"{selected_student_log}님의 활동 로그")
            logs = ast.literal_eval(data.at[student_index_log, "기록"])
            for log in logs:
                timestamp = log["timestamp"]
                activity = log["activity"]
                reward = log.get("reward", "")
                additional_info = log.get("additional_info", "")
                log_text = f"🕒 {timestamp} - {activity}"
                if reward:
                    log_text += f" (보상: {reward})"
                if additional_info:
                    log_text += f" [{additional_info}]"
                st.write(log_text)
        else:
            st.error("올바른 비밀번호를 입력하세요.")

st.markdown('</div>', unsafe_allow_html=True)
