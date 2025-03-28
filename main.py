import streamlit as st
import pandas as pd
import ast
from datetime import datetime
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
    
    # 👉 Google Sheets URL 사용
    sheet_url = st.secrets["general"]["spreadsheet"]  # secrets.toml 파일에서 불러오기
    sheet = client.open_by_url(sheet_url).sheet1  # 첫 번째 시트 선택
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
    save_data_to_cache(data)  # 캐시에 저장하여 후속 호출에 대비

# 기록을 추가하는 함수
def add_record(student_index, activity, reward=None, additional_info=None):
    record_list = ast.literal_eval(data.at[student_index, "기록"])
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    new_record = {
        "timestamp": timestamp,
        "activity": activity,
        "reward": reward,
        "additional_info": additional_info
    }
    record_list.append(new_record)
    data.at[student_index, "기록"] = str(record_list)

# --- 🌟 UI 스타일 --- 
st.markdown(
    """
    <style>
    .stApp {
        background-image: url("https://images.unsplash.com/photo-1614285260465-616bc589d90d?ixlib=rb-4.0.3&auto=format&fit=crop&w=1920&q=80");
        background-size: cover;
        background-position: center;
        background-repeat: no-repeat;
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
    </style>
    """,
    unsafe_allow_html=True
)
)

# 헤더 비트코인 GIF 이미지
st.markdown(
    '<div style="text-align:center;">'
    '<img class="header-img" src="https://media1.giphy.com/media/v1.Y2lkPTc5MGI3NjExemVldTNsMGVpMjZzdjhzc3hnbzl0d2szYjNoNXY2ZGt4ZXVtNncyciZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/30VBSGB7QW1RJpNcHO/giphy.gif" alt="Bitcoin GIF">'
    '</div>',
    unsafe_allow_html=True
)

# --- 🎓 UI 선택 --- 
user_type = st.sidebar.radio("모드를 선택하세요", ["학생용", "교사용", "통계용", "로그 확인"])

# 데이터 로드
data = load_data()

if user_type == "로그 확인":
    # --- 📝 로그 확인 기능 추가 ---
    st.sidebar.subheader("📜 로그 확인")

    selected_class_log = st.sidebar.selectbox("🔍 로그 확인용 반 선택:", data["반"].unique(), key="log_class")
    filtered_data_log = data[data["반"] == selected_class_log]
    selected_student_log = st.sidebar.selectbox("🔍 로그 확인용 학생 선택:", filtered_data_log["학생"].tolist(), key="log_student")

    # 선택한 학생의 로그 불러오기
    student_index_log = data[(data["반"] == selected_class_log) & (data["학생"] == selected_student_log)].index[0]
    student_logs = ast.literal_eval(data.at[student_index_log, "기록"])

    st.subheader(f"{selected_student_log}의 활동 로그")

    for log in student_logs:
        timestamp = log["timestamp"]
        activity = log["activity"]
        reward = log.get("reward", "")
        additional_info = log.get("additional_info", "")
    
        log_time = datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S")
        log_hour = log_time.hour

        log_text = f"🕒 {timestamp} - {activity}"
        if reward:
            log_text += f" (보상: {reward})"
        if additional_info:
            log_text += f" [{additional_info}]"

        # 오후 5시 이후 "세진코인 변경" 로그는 빨간색으로 표시
        if activity == "세진코인 변경" and log_hour >= 17:
            st.markdown(f"<span style='color:red;'>{log_text}</span>", unsafe_allow_html=True)
        else:
            st.write(log_text)


# --- 🎓 교사용 UI ---
if user_type == "교사용":
    selected_class = st.selectbox("반을 선택하세요:", data["반"].unique())
    filtered_data = data[data["반"] == selected_class]
    selected_student = st.selectbox("학생을 선택하세요:", filtered_data["학생"].tolist())
    student_index = data[(data["반"] == selected_class) & (data["학생"] == selected_student)].index[0]

    password = st.text_input("관리자 비밀번호를 입력하세요:", type="password")
    if password == st.secrets["general"]["admin_password"]:
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

        # **학생 비밀번호 변경 기능 (공백 입력도 허용)**
        st.subheader(f"🔑 {selected_student}의 비밀번호 변경")
        new_password = st.text_input("새로운 비밀번호 입력:", type="password")  # 버튼 외부에서 먼저 정의

        if st.button("비밀번호 변경"):
            # 공백 입력도 허용하므로 조건 제거
            data.at[student_index, "비밀번호"] = new_password
            save_data(data)
            st.success(f"{selected_student}의 비밀번호가 성공적으로 변경되었습니다!")


        if st.button("⚠️ 세진코인 초기화"):
            
            data.at[student_index, "세진코인"] = 0
            data.at[student_index, "기록"] = "[]"
            add_record(student_index, "세진코인 초기화", reward=None, additional_info="세진코인 및 기록 초기화")
            save_data(data)
            st.error(f"{selected_student}의 세진코인이 초기화되었습니다.")

        updated_student_data = data.loc[[student_index]].drop(columns=["비밀번호"])
        st.subheader(f"{selected_student}의 업데이트된 세진코인")
        st.dataframe(updated_student_data)

   
    student_coins = int(data.at[student_index, "세진코인"])  
    # ✅ 사이드바에 학생 정보 표시 추가
    st.sidebar.markdown("---")
    st.sidebar.subheader("📌 학생 정보")
    st.sidebar.write(f"**이름:** {selected_student}")
    st.sidebar.write(f"**보유 코인:** {student_coins}개")
    st.sidebar.markdown("---")

    st.markdown(f"<h2>{selected_student}님의 세진코인은 {student_coins}개입니다.</h2>", unsafe_allow_html=True)
# --- 🎒 학생용 UI --- 
elif user_type == "학생용":
    selected_class = st.selectbox("반을 선택하세요:", data["반"].unique())
    filtered_data = data[data["반"] == selected_class]
    selected_student = st.selectbox("학생을 선택하세요:", filtered_data["학생"].tolist())
    student_index = data[(data["반"] == selected_class) & (data["학생"] == selected_student)].index[0]

    student_coins = int(data.at[student_index, "세진코인"])
    st.markdown(f"<h2>{selected_student}님의 세진코인은 {student_coins}개입니다.</h2>", unsafe_allow_html=True)

    password = st.text_input("비밀번호를 입력하세요:", type="password")

    if password == str(data.at[student_index, "비밀번호"]):
        # --- 🎰 로또 시스템 --- 
        st.subheader("🎰 세진코인 로또 게임 (1코인 차감)")
        chosen_numbers = st.multiselect("1부터 20까지 숫자 중 **3개**를 선택하세요:", list(range(1, 21)))

        if len(chosen_numbers) == 3 and st.button("로또 게임 시작 (1코인 차감)", key="lotto_button"):
            # 4초 대기 후 로또 진행
            with st.spinner("잠시만 기다려 주세요... 로또 진행 중입니다."):
                if student_coins < 1:
                    st.error("세진코인이 부족하여 로또를 진행할 수 없습니다.")
                else:
                    # 로또 추첨 진행
                    data.at[student_index, "세진코인"] -= 1
                    pool = list(range(1, 21))
                    main_balls = random.sample(pool, 3)
                    bonus_ball = random.choice([n for n in pool if n not in main_balls])

                    st.write("**컴퓨터 추첨 결과:**")
                    st.write("메인 볼:", sorted(main_balls))
                    st.write("보너스 볼:", bonus_ball)

                    # 당첨 확인 및 보상 제공
                    matches = set(chosen_numbers) & set(main_balls)
                    match_count = len(matches)

                    reward = None
                    if match_count == 3:
                        st.success("🎉 1등 당첨! 상품: 치킨")
                        reward = "치킨"
                    elif match_count == 2 and list(set(chosen_numbers) - matches)[0] == bonus_ball:
                        st.success("🎉 2등 당첨! 상품: 햄버거세트")
                        reward = "햄버거세트"
                    elif match_count == 2:
                        st.success("🎉 3등 당첨! 상품: 매점이용권")
                        reward = "매점이용권"
                    elif match_count == 1:
                        st.success("🎉 4등 당첨! 보상: 0.5코인")
                        reward = "0.5코인"
                        data.at[student_index, "세진코인"] += 0.5
                    else:
                        st.error("😢 아쉽게도 당첨되지 않았습니다.")

                    add_record(student_index, "로또", reward, f"당첨번호: {main_balls}")
                    save_data(data)
                    st.success(f"당첨 결과: {reward}!")
                    
    student_coins = int(data.at[student_index, "세진코인"])  
    # ✅ 사이드바에 학생 정보 표시 추가
    st.sidebar.markdown("---")
    st.sidebar.subheader("📌 학생 정보")
    st.sidebar.write(f"**이름:** {selected_student}")
    st.sidebar.write(f"**보유 코인:** {student_coins}개")
    st.sidebar.markdown("---")


# --- 📊 통계용 UI --- 
elif user_type == "통계용":
    st.subheader("📊 로또 당첨 통계")

    reward_stats = {
        "치킨": 0,
        "햄버거세트": 0,
        "매점이용권": 0,
        "0.5코인": 0
    }

    # 3등 이상 당첨자 목록 필터링
    winners = data[data["기록"].str.contains("로또")]

    for index, row in winners.iterrows():
        records = ast.literal_eval(row["기록"])
        for record in records:
            if record.get("reward") in reward_stats:
                reward_stats[record["reward"]] += 1

    st.write("전체 당첨 횟수:")
    st.write(reward_stats)

    # 3등 이상 당첨자 목록 출력
    st.write("3등 이상 당첨자 목록:")
    winners_list = []
    for index, row in winners.iterrows():
        records = ast.literal_eval(row["기록"])
        for record in records:
            if record.get("reward") in ["치킨", "햄버거세트", "매점이용권"]:
                winners_list.append({
                    "학생": row["학생"],
                    "당첨 보상": record["reward"],
                    "당첨 날짜": record["timestamp"]
                })
    st.write(pd.DataFrame(winners_list))

    st.write("로또 당첨 분석이 완료되었습니다.")
