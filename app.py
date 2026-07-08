import re
from collections import Counter

import pdfplumber
import streamlit as st
from docx import Document
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


st.set_page_config(
    page_title="ATS Resume Evaluation System",
    page_icon="📄",
    layout="wide"
)


def extract_text_from_pdf(uploaded_file):
    text = ""

    with pdfplumber.open(uploaded_file) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"

    return text


def extract_text_from_docx(uploaded_file):
    document = Document(uploaded_file)
    text = ""

    for paragraph in document.paragraphs:
        text += paragraph.text + "\n"

    return text


def clean_text(text):
    text = text.lower()
    text = re.sub(r"[^a-zA-Z0-9\s+#.]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def calculate_match_score(resume_text, job_description):
    documents = [resume_text, job_description]

    vectorizer = TfidfVectorizer(stop_words="english")
    tfidf_matrix = vectorizer.fit_transform(documents)

    similarity = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
    score = round(similarity * 100, 2)

    return score


def extract_keywords(text):
    text = clean_text(text)
    words = text.split()

    stop_words = {
        "and", "or", "the", "a", "an", "to", "for", "of", "in", "on", "with",
        "is", "are", "be", "as", "by", "from", "this", "that", "will", "you",
        "your", "we", "our", "have", "has", "experience", "role", "work",
        "candidate", "team", "company", "job"
    }

    keywords = []

    for word in words:
        if word not in stop_words and len(word) > 2:
            keywords.append(word)

    return Counter(keywords).most_common(30)


def find_missing_keywords(resume_text, job_description):
    resume_words = set(clean_text(resume_text).split())
    job_keywords = extract_keywords(job_description)

    missing_keywords = []

    for keyword, count in job_keywords:
        if keyword not in resume_words:
            missing_keywords.append(keyword)

    return missing_keywords[:15]


def give_suggestions(score, missing_keywords):
    suggestions = []

    if score < 40:
        suggestions.append("Your resume match is low. Add more job-related skills and keywords from the job description.")
    elif score < 70:
        suggestions.append("Your resume has a moderate match. Improve your project descriptions and include more relevant tools.")
    else:
        suggestions.append("Your resume has a good match. Make sure your achievements are clear and measurable.")

    if missing_keywords:
        suggestions.append("Add missing keywords naturally in your Skills, Projects, or Experience section.")
        suggestions.append("Do not copy keywords randomly. Only add skills that you actually know.")

    suggestions.append("Use strong action words such as developed, implemented, analysed, designed, and improved.")
    suggestions.append("Add measurable results where possible, such as accuracy, performance improvement, or number of records processed.")

    return suggestions


st.title("📄 ATS Resume Evaluation System")

st.write(
    "Upload your resume and paste a job description. "
    "The system will calculate an ATS-style match score and show missing keywords."
)

col1, col2 = st.columns(2)

with col1:
    uploaded_resume = st.file_uploader(
        "Upload Resume",
        type=["pdf", "docx"]
    )

with col2:
    job_description = st.text_area(
        "Paste Job Description",
        height=250,
        placeholder="Paste the job description here..."
    )


if st.button("Evaluate Resume"):
    if uploaded_resume is None:
        st.error("Please upload your resume.")
    elif not job_description.strip():
        st.error("Please paste the job description.")
    else:
        file_type = uploaded_resume.name.split(".")[-1].lower()

        if file_type == "pdf":
            resume_text = extract_text_from_pdf(uploaded_resume)
        elif file_type == "docx":
            resume_text = extract_text_from_docx(uploaded_resume)
        else:
            st.error("Unsupported file type.")
            st.stop()

        if not resume_text.strip():
            st.error("Could not read the resume. Please upload a text-based PDF or DOCX file.")
            st.stop()

        cleaned_resume = clean_text(resume_text)
        cleaned_job_description = clean_text(job_description)

        score = calculate_match_score(cleaned_resume, cleaned_job_description)
        missing_keywords = find_missing_keywords(cleaned_resume, cleaned_job_description)
        suggestions = give_suggestions(score, missing_keywords)

        st.subheader("ATS Match Score")

        if score >= 70:
            st.success(f"{score}% Match")
        elif score >= 40:
            st.warning(f"{score}% Match")
        else:
            st.error(f"{score}% Match")

        st.progress(score / 100)

        st.subheader("Missing Keywords")

        if missing_keywords:
            st.write(", ".join(missing_keywords))
        else:
            st.write("No major missing keywords found.")

        st.subheader("Suggestions to Improve Resume")

        for suggestion in suggestions:
            st.write("- " + suggestion)

        with st.expander("View Extracted Resume Text"):
            st.write(resume_text)



