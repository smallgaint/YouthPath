import streamlit as st
import requests

st.title("YouthPath")

name = st.text_input("이름")
job = st.text_input("관심 직무")

if st.button("제출"):
    response = requests.get("http://127.0.0.1:8000/")
    st.write(response.json())