import streamlit as st
import io
import re
import pandas as pd
import matplotlib.pyplot as plt
from PyPDF2 import PdfReader
import docx
from fpdf import FPDF

# ----------------------------
# 1️⃣ Helper Functions
# ----------------------------
def read_pdf(file):
    pdf_reader = PdfReader(file)
    return "\n".join([page.extract_text() for page in pdf_reader.pages if page.extract_text()])

def read_docx(file):
    doc = docx.Document(file)
    return "\n".join([para.text for para in doc.paragraphs])

def get_text_from_upload(uploaded_file):
    if uploaded_file.name.endswith(".pdf"):
        return read_pdf(uploaded_file)
    elif uploaded_file.name.endswith(".docx"):
        return read_docx(uploaded_file)
    elif uploaded_file.name.endswith(".txt"):
        return uploaded_file.read().decode("utf-8")
    else:
        return ""

def extract_keywords(text):
    words = re.findall(r'\b\w+\b', text.lower())
    stopwords = set([
        "and", "or", "the", "a", "to", "of", "in", "for", "on", "at", "by", "with",
        "an", "is", "are", "this", "that", "from", "as", "be", "it", "have", "has"
    ])
    keywords = [w for w in words if w not in stopwords and len(w) > 2]
    return keywords

def match_and_prioritize(resume_text, jd_text):
    resume_keywords = extract_keywords(resume_text)
    jd_keywords = extract_keywords(jd_text)

    keyword_freq = {}
    for kw in jd_keywords:
        if kw in resume_keywords:
            keyword_freq[kw] = keyword_freq.get(kw, 0) + 1

    sorted_keywords = sorted(keyword_freq.items(), key=lambda x: x[1], reverse=True)
    return sorted_keywords

def highlight_resume(resume_text, keywords):
    highlighted = resume_text
    for kw, _ in keywords:
        highlighted = re.sub(rf"\b({kw})\b", r"**\1**", highlighted, flags=re.IGNORECASE)
    return highlighted

def keyword_density_heatmap(keywords):
    df = pd.DataFrame(keywords, columns=["Keyword", "Frequency"])
    fig, ax = plt.subplots()
    df.plot(kind="barh", x="Keyword", y="Frequency", ax=ax, legend=False)
    plt.xlabel("Frequency")
    plt.ylabel("Keyword")
    plt.title("Keyword Density Heatmap")
    st.pyplot(fig)

def save_as_pdf(text, filename="optimized_resume.pdf"):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    for line in text.split("\n"):
        pdf.multi_cell(0, 10, line)
    pdf.output(filename)
    return filename

# ----------------------------
# 2️⃣ Streamlit App UI
# ----------------------------
st.title("Resume Optimizer with JD Keyword Matching")
st.markdown("**Modular** – can integrate with future company role analysis automation.")

# Resume upload
st.subheader("Upload Your Resume")
resume_file = st.file_uploader("Upload resume (PDF/DOCX)", type=["pdf", "docx"])

# JD upload or paste
st.subheader("Upload or Paste Job Description")
jd_file = st.file_uploader("Upload JD (PDF/DOCX/TXT)", type=["pdf", "docx", "txt"])
jd_text_input = st.text_area("Or paste JD here", height=250)

# Extract text
resume_text = ""
jd_text = ""

if resume_file:
    resume_text = get_text_from_upload(resume_file)

if jd_file:
    jd_text = get_text_from_upload(jd_file)
elif jd_text_input.strip():
    jd_text = jd_text_input.strip()

# Processing
if resume_text and jd_text:
    st.success("Both Resume and Job Description loaded successfully!")

    keywords = match_and_prioritize(resume_text, jd_text)
    st.write("### Matched & Prioritized Keywords", keywords)

    st.write("### Keyword Density Heatmap")
    keyword_density_heatmap(keywords)

    highlighted_resume = highlight_resume(resume_text, keywords)

    st.write("### Optimized Resume Preview")
    st.markdown(highlighted_resume)

    pdf_path = save_as_pdf(highlighted_resume)
    with open(pdf_path, "rb") as f:
        st.download_button("Download Optimized Resume (PDF)", f, file_name="optimized_resume.pdf", mime="application/pdf")

else:
    st.warning("Please provide both Resume and Job Description to proceed.")
