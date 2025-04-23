import streamlit as st
import fitz  # PyMuPDF
import pytesseract
from docx import Document
from io import BytesIO
from PIL import Image
import numpy as np

# Optional: Windows path
# pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

def pdf_pages_to_images(pdf_bytes):
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    images = []

    for page in doc:
        pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))  # higher resolution
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        images.append(img)

    return images

def ocr_text_from_image(image, lang='rus'):
    return pytesseract.image_to_string(image, lang=lang)

def generate_docx(images, included_flags, lang='rus', progress_callback=None):
    doc = Document()
    total = sum(included_flags)
    done = 0

    for i, (image, include) in enumerate(zip(images, included_flags)):
        if include:
            text = pytesseract.image_to_string(image, lang=lang)
            doc.add_paragraph(text)
            doc.add_page_break()
            done += 1
            if progress_callback:
                progress_callback(done, total)

    output = BytesIO()
    doc.save(output)
    output.seek(0)
    return output

# --- UI ---
st.title("📄 PDF OCR with Page Selection and Text Preview")

lang_choice = st.selectbox("Choose OCR language", ["rus", "eng", "rus+eng"], index=0)
uploaded_file = st.file_uploader("Upload a scanned PDF file", type="pdf")

if uploaded_file:
    st.info("🔄 Converting PDF to images...")
    images = pdf_pages_to_images(uploaded_file.read())
    included_flags = [False] * len(images)  # Track included pages
    st.write(f"Found {len(images)} pages.")

    st.markdown("### 📖 Preview Pages and OCR Text")

    for i in range(0, len(images), 2):
        cols = st.columns(2)

        for j in range(2):
            idx = i + j
            if idx >= len(images):
                break

            with cols[j]:
                st.image(images[idx], caption=f"Page {idx+1}", use_container_width=True)
                included_flags[idx] = st.checkbox(f"Include Page {idx+1}", value=True, key=f"include_{idx}")

                if included_flags[idx]:
                    with st.spinner(f"OCR Page {idx+1}..."):
                        text = ocr_text_from_image(images[idx], lang=lang_choice)
                    st.text_area(f"OCR Text Preview (Page {idx+1})", value=text, height=200, key=f"text_{idx}")

    if any(included_flags):
        if st.button("📥 Generate DOCX from Selected Pages"):
            progress_bar = st.progress(0)
            status_text = st.empty()

            def update_progress(current, total):
                percent = int(current / total * 100)
                progress_bar.progress(percent)
                status_text.text(f"Generating DOCX: Page {current} of {total}")

            with st.spinner("Running final OCR and generating DOCX..."):
                docx_file = generate_docx(images, included_flags, lang=lang_choice, progress_callback=update_progress)

            st.success("✅ DOCX Ready!")
            st.download_button(
                label="📄 Download DOCX",
                data=docx_file,
                file_name="converted_output.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            )
    else:
        st.warning("⚠️ No pages selected for export.")

