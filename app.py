import streamlit as st
import re
from PyPDF2 import PdfReader
from fpdf import FPDF
import tempfile
import os
from datetime import datetime

# -----------------------------
# Helper Functions
# -----------------------------

def extract_text_from_pdf(uploaded_file):
    """Extract text from uploaded PDF."""
    pdf_reader = PdfReader(uploaded_file)
    text = ""
    for page in pdf_reader.pages:
        text += page.extract_text() + "\n"
    return text

def save_as_pdf(highlighted_text, filename="optimized_resume.pdf"):
    """Save highlighted resume as PDF."""
    pdf = FPDF()
    pdf.add_page()

    # Use a basic font (works on Streamlit Cloud without TTF files)
    pdf.set_font("Arial", size=11)

    # Remove markdown **bold** markers for plain PDF output
    clean_text = re.sub(r"\*\*(.*?)\*\*", r"\1", highlighted_text)

    # MultiCell for proper wrapping
    pdf.multi_cell(0, 8, clean_text)

    temp_dir = tempfile.gettempdir()
    file_path = os.path.join(temp_dir, filename)
    pdf.output(file_path)
    return file_path

def highlight_keywords(text, keywords):
    """Highlight keywords in resume using markdown bold."""
    for word in sorted(keywords, key=len, reverse=True):
        pattern = r'\b(' + re.escape(word) + r')\b'
        text = re.sub(pattern, r'**\1**', text, flags=re.IGNORECASE)
    return text

def process_resume(jd_text, resume_text):
    """Main processing: match keywords, prioritize, highlight."""
    jd_words = re.findall(r'\b\w+\b', jd_text.lower())
    resume_words = re.findall(r'\b\w+\b', resume_text.lower())

    keyword_freq = {}
    for word in jd_words:
        if len(word) > 2:  # skip short words
            keyword_freq[word] = keyword_freq.get(word, 0) + resume_words.count(word)

    matched_keywords = sorted(keyword_freq.items(), key=lambda x: (-x[1], x[0]))

    matched_only = [kw for kw, count in matched_keywords if count > 0]
    highlighted_resume = highlight_keywords(resume_text, matched_only)

    return matched_keywords, keyword_freq, highlighted_resume

# -----------------------------
# Streamlit UI
# -----------------------------

st.set_page_config(page_title="Resume Optimiser", layout="wide")

# Sidebar history display
st.sidebar.title("📜 History")
if "history" not in st.session_state:
    st.session_state.history = []

if st.session_state.history:
    for i, record in enumerate(reversed(st.session_state.history), start=1):
        st.sidebar.markdown(f"**{i}. {record['jd_title']}**  
        ⏱ {record['timestamp']}  
        🗝 {record['keyword_count']} keywords matched")
else:
    st.sidebar.write("No history yet. Generate a resume to see history here.")

# Main title
st.title("📄 Resume Optimiser & Keyword Highlighter")

st.markdown("""
Upload your **resume (PDF)** and either **paste** or **upload** a Job Description.  
Click **Generate Optimized Resume** to get:
1. Matched & prioritized keywords
2. Keyword density heatmap
3. Optimized resume PDF with highlights
""")

# Job Description input
jd_text = st.text_area("📌 Paste Job Description", height=200)
jd_file = st.file_uploader("📂 Or Upload Job Description (PDF/TXT)", type=["pdf", "txt"])

if jd_file is not None:
    if jd_file.type == "application/pdf":
        jd_text = extract_text_from_pdf(jd_file)
    else:
        jd_text = jd_file.read().decode("utf-8")

# Resume upload
uploaded_resume = st.file_uploader("📄 Upload Your Resume (PDF)", type="pdf")

# Process button
if st.button("🚀 Generate Optimized Resume"):
    if uploaded_resume and jd_text.strip():
        resume_text = extract_text_from_pdf(uploaded_resume)

        matched_keywords, heatmap, highlighted_resume = process_resume(jd_text, resume_text)

        st.subheader("📊 Matched & Prioritized Keywords")
        st.json(matched_keywords)

        st.subheader("🔥 Keyword Density Heatmap (Word : Count)")
        st.json(heatmap)

        st.subheader("📝 Optimized Resume Preview (with highlighted keywords)")
        st.markdown(highlighted_resume, unsafe_allow_html=True)

        # Save PDF & download
        pdf_path = save_as_pdf(highlighted_resume)
        with open(pdf_path, "rb") as pdf_file:
            st.download_button(
                label="⬇️ Download Optimized Resume (PDF)",
                data=pdf_file,
                file_name="optimized_resume.pdf",
                mime="application/pdf"
            )

        # Save history
        jd_title = jd_text.strip().split("\n")[0][:50] + "..."
        st.session_state.history.append({
            "jd_title": jd_title,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "keyword_count": len([kw for kw, count in matched_keywords if count > 0])
        })

    else:
        st.warning("⚠️ Please upload your resume and provide the Job Description first.")
