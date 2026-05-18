import streamlit as st
import requests

st.title("Clinical Orientation System")

case = st.text_area("Décrire le cas patient")

if st.button("Démarrer"):

    response = requests.post(
        "http://127.0.0.1:8000/consultation/start",
        json={"patient_case": case}
    )

    st.write("STATUS:", response.status_code)
    st.write("RAW RESPONSE:")
    st.text(response.text)

    try:
        st.json(response.json())
    except Exception as e:
        st.error("Backend did not return valid JSON ")