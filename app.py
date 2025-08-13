import streamlit as st
import io
from PyPDF2 import PdfReader
from fpdf import FPDF
import re
from collections import Counter

# ----------------------
# PDF Text Extraction
# ----------------------
def extract_text_from_pdf(file):
    reader = PdfReader(file)
    text = ""
    for page in reader.pages:
        text += page.extract_text() + "\n"
    return text

# ----------------------
# Save as PDF (fixed for Streamlit Cloud)
# ----------------------
def save_as_pdf(text):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    # Ensure PDF encoding compatibility
    safe_text = text.encode('latin-1', 'replace').decode('latin-1')
    for line in safe_text.split("\n"):
        pdf.multi_cell(0, 8, line)

    # Return BytesIO for download
    pdf_bytes = pdf.output(dest='S').encode('latin-1')
    return io.BytesIO(pdf_bytes)

# ----------------------
# Keyword Matching
# ----------------------
def match_keywords(jd_text, resume_text):
    jd_words = re.findall(r'\w+', jd_text.lower())
    resume_words = re.findall(r'\w+', resume_text.lower())
    jd_counts = Counter(jd_words)

    matched_keywords = []
    for word, count in jd_counts.items():
        if word in resume_words and len(word) > 2:
            matched_keywords.append((word, resume_words.count(word)))

    matched_keywords.sort(key=lambda x: (-x[1], x[0]))  # Priority by frequency
    return matched_keywords

# ----------------------
# Highlight Keywords in Resume
# ----------------------
def highlight_resume(resume_text, keywords):
    for kw, _ in keywords:
        resume_text = re.sub(rf"\b({kw})\b", r"**\1**", resume_text, flags=re.IGNORECASE)
    return resume_text

# ----------------------
# Streamlit UI
# ----------------------
st.set_page_config(page_title="Resume Optimiser", layout="wide")

st.title("📄 Resume Optimiser")

# Sidebar History
if "history" not in st.session_state:
    st.session_state.history = []

st.sidebar.header("📜 History")
if st.session_state.history:
    for i, record in enumerate(st.session_state.history, 1):
        st.sidebar.markdown(f"**{i}. {record['jd_title']}**")
        st.sidebar.caption(f"Keywords matched: {len(record['keywords'])}")
else:
    st.sidebar.info("No history yet.")

# Input Section
st.subheader("1️⃣ Upload Resume (PDF)")
uploaded_resume = st.file_uploader("Upload your Resume", type=["pdf"])

st.subheader("2️⃣ Provide Job Description")
jd_option = st.radio("Choose input method", ["Paste JD", "Upload JD PDF"])
jd_text = ""
if jd_option == "Paste JD":
    jd_text = st.text_area("Paste the Job Description here")
else:
    uploaded_jd = st.file_uploader("Upload JD PDF", type=["pdf"])
    if uploaded_jd:
        jd_text = extract_text_from_pdf(uploaded_jd)

# Process Button
if st.button("🚀 Optimise Resume"):
    if uploaded_resume and jd_text.strip():
        resume_text = extract_text_from_pdf(uploaded_resume)

        # Keyword matching
        keywords = match_keywords(jd_text, resume_text)

        # Highlighted resume
        highlighted_resume = highlight_resume(resume_text, keywords)

        # Save PDF
        pdf_output = save_as_pdf(highlighted_resume)

        # Show results
        st.success("✅ Resume optimised successfully!")
        st.subheader("Matched & Prioritised Keywords")
        st.write(keywords)

        st.subheader("Optimised Resume Preview")
        st.markdown(highlighted_resume)

        # Download button
        st.download_button(
            label="📥 Download Optimised Resume (PDF)",
            data=pdf_output,
            file_name="optimised_resume.pdf",
            mime="application/pdf"
        )

        # Save to history
        st.session_state.history.append({
            "jd_title": jd_text[:40] + "...",
            "keywords": keywords,
            "resume_preview": highlighted_resume
        })

    else:
        st.error("⚠ Please upload your resume and provide a job description.")
