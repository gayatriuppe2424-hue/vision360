import streamlit as st

st.set_page_config(
    page_title="Vision360",
    page_icon="👁️",
    layout="wide"
)

st.title("👁️ Vision360")
st.subheader("Hands-Free Computer Interaction & Digital Wellness")

st.write(
    "Vision360 is a webcam-based accessibility project designed "
    "to explore hands-free computer interaction and digital wellness."
)

st.divider()

st.header("Explore Vision360")

tab1, tab2, tab3 = st.tabs([
    "Head Movement Control",
    "Dwell Clicking",
    "Digital Wellness"
])

with tab1:
    st.subheader("Head Movement Control")
    st.write(
        "Explore how head movements can be used to navigate "
        "a computer interface without a traditional mouse."
    )
    st.info(
        "Interactive webcam tracking will be integrated in a later step."
    )

with tab2:
    st.subheader("Dwell Clicking")
    st.write(
        "Dwell clicking triggers a click when the cursor remains "
        "over a target for a configured duration."
    )
    st.info(
        "Browser-based dwell clicking will be integrated in a later step."
    )

with tab3:
    st.subheader("Digital Wellness")
    st.write(
        "Explore ideas for screen-use monitoring, eye-rest reminders, "
        "and healthier computer-use habits."
    )

st.divider()

st.subheader("Technology Stack")
st.write("Python • OpenCV • MediaPipe • Streamlit")

st.caption("Vision360 — College Project")