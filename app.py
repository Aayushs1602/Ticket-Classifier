import streamlit as st
from classifier import classify_ticket

st.title("VibeFI AI Ticket Classifier")
st.write("Classify incoming banking support tickets into AI Patch or Vibe Workflow, with AI-generated reasoning and checklist.")

with st.form("ticket_form"):
    channel = st.text_area("Channel", "")
    severity = st.selectbox("Severity", ["low", "medium", "high"])
    summary = st.text_area("Ticket Summary", "")
    submitted = st.form_submit_button("Classify Ticket")
if summary and channel:
    if submitted:
        ticket = {
            "channel": channel,
            "severity": severity,
            "summary": summary
        }

        with st.spinner("Classifying and generating reasoning..."):
            result = classify_ticket(ticket)

        st.subheader("Decision")
        st.success(result["decision"])

        st.subheader("Reasoning")
        st.write(result["reasoning"])

        st.subheader("Checklist")
        for step in result["checklist"]:
            st.write(f"- {step}")
