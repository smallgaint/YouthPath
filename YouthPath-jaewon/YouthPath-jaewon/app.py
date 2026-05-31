import streamlit as st
import requests

st.title("YouthPath")

name = st.text_input("이름")
age = st.number_input("나이", min_value=0, max_value=100, value=27)
region = st.text_input("지역", value="서울")
job = st.text_input("관심 직무", value="데이터 분석가")
company = st.text_input("관심 기업", value="네이버")
query = st.text_input("질의", value="서울에서 월세 도와주는 정책이랑 IT 신입 공고 알려줘")

if st.button("제출"):
    payload = {
        "query": query,
        "profile": {
            "name": name,
            "age": int(age),
            "region": region,
            "target_role": job,
            "target_company": company,
            "skills": ["Python", "SQL"],
            "income_bracket": 60,
            "experience_y": 0,
        },
    }
    response = requests.post("http://127.0.0.1:8000/ask", json=payload, timeout=60)
    st.write(response.json())