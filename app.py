import streamlit as st
import re
from collections import Counter
from PyPDF2 import PdfReader
from fpdf import FPDF
import os

# ------------------ PDF SAVE FUNCTION (Unicode Safe) ------------------ #
def save_as_pdf(text, filename="optimized_resume.pdf"):
    pdf = FPDF()
    pdf.add_page()
    # Add a Unicode font (must have DejaVuSans.ttf in the project folder)
    pdf.add_font("DejaVu", "", "DejaVuSans.ttf", uni=True)
    pdf.set_font("DejaVu", size=12)

    for line in text.split("\n"):
        pdf.multi_cell(0, 8, line)

    pdf.output(filename)
    return filename

# ------------------ TEXT EXTRACTION ------------------ #
def extract_text_from_pdf(uploaded_file):
    reader = PdfReader(uploaded_file)
    text = ""
    for page in reader.pages:
        text += page.extract_text() + "\n"
    return text.strip()

# ------------------ KEYWORD MATCHING ------------------ #
def keyword_matching(resume_text, jd_text):
    resume_words = re.findall(r'\b\w+\b', resume_text.lower())
    jd_words = re.findall(r'\b\w+\b', jd_text.lower())
    jd_word_counts = Counter(jd_words)

    matched_keywords = [(word, jd_word_counts[word]) for word in set(resume_words) if word in jd_word_counts]
    matched_keywords.sort(key=lambda x: (-x[1], x[0]))
    return matched_keywords

# ------------------ HIGHLIGHT MATCHES ------------------ #
def highlight_keywords(resume_text, matched_keywords):
    highlighted = resume_text
    for keyword, _ in matched_keywords:
        highlighted = re.sub(rf'\b({keyword})\b', r'**\1**', highlighted, flags=re.IGNORECASE)
    return highlighted

# ------------------ STREAMLIT UI ------------------ #
st.title("📄 Resume Optimiser & Keyword Highlighter")

st.sidebar.header("Upload Your Files")
jd_input_option = st.sidebar.radio("Job Description Input:", ["Paste Text", "Upload PDF"])

if jd_input_option == "Paste Text":
    jd_text = st.text_area("Paste the Job Description here:")
else:
    jd_file = st.file_uploader("Upload Job Description PDF", type=["pdf"])
    jd_text = extract_text_from_pdf(jd_file) if jd_file else ""

resume_file = st.sidebar.file_uploader("Upload Resume PDF", type=["pdf"])
resume_text = extract_text_from_pdf(resume_file) if resume_file else ""

if jd_text and resume_text:
    matched_keywords = keyword_matching(resume_text, jd_text)
    st.subheader("Matched & Prioritized Keywords")
    st.write(matched_keywords)

    highlighted_resume = highlight_keywords(resume_text, matched_keywords)

    st.subheader("Optimized Resume Preview")
    st.text_area("", highlighted_resume, height=400)

    # Save as PDF with Unicode font
    pdf_path = save_as_pdf(highlighted_resume)
    with open(pdf_path, "rb") as pdf_file:
        st.download_button(
            label="📥 Download Optimized Resume (PDF)",
            data=pdf_file,
            file_name="optimized_resume.pdf",
            mime="application/pdf"
        )

    st.info("✅ Modular design — ready for integration with Task 3: Automated Company Role Analysis")

else:
    st.warning("Please upload both Resume & Job Description to continue.")
