import re
import streamlit as st
import PyPDF2
import nltk

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from nltk.corpus import stopwords

from database import init_db
from auth import register_user, login_user, save_analysis, get_user_history

nltk.download("stopwords", quiet=True)
STOPWORDS = set(stopwords.words("english"))

st.set_page_config(page_title="AI Resume Screening System", layout="wide")

init_db()

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "user_id" not in st.session_state:
    st.session_state.user_id = None
if "username" not in st.session_state:
    st.session_state.username = None


def extract_text_from_pdf(uploaded_file):
    text = ""
    pdf_reader = PyPDF2.PdfReader(uploaded_file)
    for page in pdf_reader.pages:
        content = page.extract_text()
        if content:
            text += content + " "
    return text


def clean_text(text):
    text = text.lower()
    text = re.sub(r"[^a-zA-Z0-9\s]", " ", text)
    words = text.split()
    words = [word for word in words if word not in STOPWORDS]
    return " ".join(words)


def get_match_score(resume_text, jd_text):
    documents = [resume_text, jd_text]
    tfidf = TfidfVectorizer()
    matrix = tfidf.fit_transform(documents)
    score = cosine_similarity(matrix[0:1], matrix[1:2])[0][0]
    return round(score * 100, 2)


def get_common_keywords(resume_text, jd_text):
    resume_words = set(resume_text.split())
    jd_words = set(jd_text.split())
    common = sorted(list(resume_words.intersection(jd_words)))
    return common[:30]


st.title("AI Resume Screening System")
st.write("Upload a resume, paste a job description, and get a match score.")

if not st.session_state.logged_in:
    menu = st.sidebar.selectbox("Menu", ["Login", "Sign Up"])

    if menu == "Sign Up":
        st.subheader("Create Account")
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")

        if st.button("Register"):
            if username.strip() and password.strip():
                success, msg = register_user(username.strip(), password.strip())
                if success:
                    st.success(msg)
                else:
                    st.error(msg)
            else:
                st.error("Username and password are required.")

    elif menu == "Login":
        st.subheader("Login")
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")

        if st.button("Login"):
            user = login_user(username.strip(), password.strip())
            if user:
                st.session_state.logged_in = True
                st.session_state.user_id = user[0]
                st.session_state.username = user[1]
                st.success(f"Welcome, {user[1]}!")
                st.rerun()
            else:
                st.error("Invalid username or password.")

else:
    menu = st.sidebar.selectbox("Menu", ["Analyzer", "History", "Logout"])

    if menu == "Analyzer":
        st.subheader(f"Welcome, {st.session_state.username}")

        uploaded_resume = st.file_uploader("Upload Resume (PDF)", type=["pdf"])
        job_description = st.text_area("Paste Job Description", height=200)

        if st.button("Analyze Resume"):
            if uploaded_resume and job_description.strip():
                resume_raw = extract_text_from_pdf(uploaded_resume)
                resume_clean = clean_text(resume_raw)
                jd_clean = clean_text(job_description)

                if not resume_clean.strip():
                    st.error("Could not extract enough text from the resume PDF.")
                else:
                    score = get_match_score(resume_clean, jd_clean)
                    keywords = get_common_keywords(resume_clean, jd_clean)
                    keywords_text = ", ".join(keywords)

                    save_analysis(
                        st.session_state.user_id,
                        uploaded_resume.name,
                        job_description,
                        score,
                        keywords_text
                    )

                    st.subheader("Match Score")
                    st.success(f"{score}%")

                    st.subheader("Matching Keywords")
                    if keywords:
                        st.write(keywords_text)
                    else:
                        st.write("No major matching keywords found.")
            else:
                st.error("Please upload a resume and paste the job description.")

    elif menu == "History":
        st.subheader("Analysis History")
        rows = get_user_history(st.session_state.user_id)

        if rows:
            for row in rows:
                st.markdown(f"### {row[0]}")
                st.write(f"**Match Score:** {row[1]}%")
                st.write(f"**Keywords:** {row[2] if row[2] else 'N/A'}")
                st.write(f"**Date:** {row[3]}")
                st.markdown("---")
        else:
            st.info("No analysis history found.")

    elif menu == "Logout":
        st.session_state.logged_in = False
        st.session_state.user_id = None
        st.session_state.username = None
        st.success("Logged out successfully.")
        st.rerun()