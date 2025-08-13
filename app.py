import streamlit as st
from PyPDF2 import PdfReader
from fpdf import FPDF
import re
import pandas as pd
from datetime import datetime
import io

# -------------------------
# PDF Saving Function
# -------------------------
def save_as_pdf(text, filename="optimized_resume.pdf"):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    # Handle Unicode properly (replace unsupported chars)
    safe_text = text.encode('latin-1', 'replace').decode('latin-1')
    for line in safe_text.split("\n"):
        pdf.multi_cell(0, 8, line)

    pdf_output = io.BytesIO()
    pdf.output(pdf_output)
    pdf_output.seek(0)
    return pdf_output

# -------------------------
# Keyword Extraction
# -------------------------
def extract_keywords(text):
    words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
    return pd.Series(words).value_counts()

# -------------------------
# Highlight Resume
# -------------------------
def highlight_resume(resume_text, keywords):
    highlighted = resume_text
    for kw in keywords:
        highlighted = re.sub(
            fr"\b({re.escape(kw)})\b",
            r"**\1**",
            highlighted,
            flags=re.IGNORECASE
        )
    return highlighted

# -------------------------
# Streamlit App Layout
# -------------------------
st.set_page_config(page_title="Resume Optimiser", layout="wide")
st.title("📄 AI Resume Optimiser with Keyword Highlighting")

# History
if "history" not in st.session_state:
    st.session_state.history = []

# JD Input Section
st.subheader("Step 1: Job Description Input")
jd_option = st.radio("Choose input method:", ["Upload JD (PDF)", "Paste JD Text"])

job_description = ""
if jd_option == "Upload JD (PDF)":
    jd_file = st.file_uploader("Upload Job Description PDF", type=["pdf"], key="jd")
    if jd_file:
        reader = PdfReader(jd_file)
        job_description = "\n".join([page.extract_text() for page in reader.pages if page.extract_text()])
elif jd_option == "Paste JD Text":
    job_description = st.text_area("Paste the Job Description here")

# Resume Upload
st.subheader("Step 2: Upload Resume")
resume_file = st.file_uploader("Upload Resume PDF", type=["pdf"], key="resume")

# Process Button
if st.button("🚀 Optimise Resume"):
    if job_description.strip() and resume_file:
        # Extract text from resume
        reader = PdfReader(resume_file)
        resume_text = "\n".join([page.extract_text() for page in reader.pages if page.extract_text()])

        # Extract keywords from JD
        jd_keywords = extract_keywords(job_description)

        # Match keywords with resume
        matched_keywords = {kw: count for kw, count in jd_keywords.items() if kw in resume_text.lower()}

        # Sort by priority (frequency in JD)
        matched_sorted = sorted(matched_keywords.items(), key=lambda x: x[1], reverse=True)

        # Highlight resume
        highlighted_resume = highlight_resume(resume_text, matched_keywords.keys())

        # Save as PDF
        pdf_output = save_as_pdf(highlighted_resume)

        # Display results
        st.subheader("Matched & Prioritized Keywords")
        st.write(matched_sorted)

        st.subheader("Keyword Density Heatmap")
        heatmap_df = pd.DataFrame(matched_sorted, columns=["Keyword", "Count"])
        st.dataframe(heatmap_df)

        st.subheader("Optimized Resume Preview")
        st.markdown(highlighted_resume)

        # Download button
        st.download_button(
            label="📥 Download Optimized Resume as PDF",
            data=pdf_output,
            file_name="optimized_resume.pdf",
            mime="application/pdf"
        )

        # Save to history
        st.session_state.history.append({
            "jd_title": job_description[:30] + "...",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "keyword_count": len(matched_sorted)
        })

    else:
        st.warning("⚠ Please upload both the Job Description and Resume.")

# -------------------------
# Sidebar History
# -------------------------
st.sidebar.title("📜 History")
if st.session_state.history:
    for i, record in enumerate(reversed(st.session_state.history), start=1):
        st.sidebar.markdown(
            f"**{i}. {record['jd_title']}**\n"
            f"⏱ {record['timestamp']}\n"
            f"🗝 {record['keyword_count']} keywords matched"
        )
else:
    st.sidebar.write("No history yet. Generate a resume to see history here.")
