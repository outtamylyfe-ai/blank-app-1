import streamlit as st
import easyocr
import numpy as np
from PIL import Image
import re
import io
from datetime import datetime
from streamlit_canvas import st_canvas

# PDF Generation imports
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image as RLImage, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

# Set page configuration
st.set_page_config(page_title="Nirvana Service Advisor Onboarding", layout="centered")

# Helper function to remove Chinese/Non-Latin characters to prevent ReportLab Helvetica crash
def clean_pdf_text(text):
    if not text:
        return ""
    # Keeps alphanumeric, punctuation, spaces, and removes characters out of standard latin range
    return re.sub(r'[^\x00-\x7F]+', '', text).strip()

# Initialize EasyOCR Reader (cached so it only loads once)
@st.cache_resource
def load_ocr():
    return easyocr.Reader(['en'])

reader = load_ocr()

# --- APP HEADER ---
st.title("富貴 NIRVANA")
st.subheader("SERVICE ADVISOR APPLICATION FORM / 代理商申请表格")
st.caption("Referencing Form: (ISO FORM) NV-SG-CSD-F01 Rev.2 Service Advisor Application Form - with effect 01.05.2023.pdf")

st.markdown("---")

# Initialize Session States
if "full_name" not in st.session_state: st.session_state.full_name = ""
if "nric_no" not in st.session_state: st.session_state.nric_no = ""
if "bank_name" not in st.session_state: st.session_state.bank_name = ""
if "bank_acc" not in st.session_state: st.session_state.bank_acc = ""

# ==========================================
# 1) TAKE / UPLOAD PHOTO OF IC (NRIC)
# ==========================================
st.markdown("### 1️⃣ NRIC Extraction / 身份证资料")
ic_source = st.radio("Choose IC Source:", ("Camera / Take Photo", "Upload File"), horizontal=True)

ic_image = None
if ic_source == "Camera / Take Photo":
    ic_image = st.camera_input("Capture front of NRIC")
else:
    ic_image = st.file_uploader("Upload NRIC Image", type=["jpg", "jpeg", "png"])

if ic_image is not None:
    try:
        img = Image.open(ic_image)
        img_np = np.array(img)
        with st.spinner("Extracting NRIC information..."):
            results = reader.readtext(img_np, detail=0)
            extracted_text = " ".join(results)
            
            nric_match = re.search(r'[STFGM]\d{7}[A-Z]', extracted_text, re.IGNORECASE)
            if nric_match:
                st.session_state.nric_no = nric_match.group(0).upper()
                st.success(f"✓ Automatically extracted NRIC: {st.session_state.nric_no}")
            
            lines = [line.strip().upper() for line in results if len(line.strip()) > 3]
            if lines:
                filtered_lines = [l for l in lines if not any(x in l for x in ["IDENTITY", "CARD", "SINGAPORE", "REPUBLIC"])]
                if filtered_lines:
                    st.session_state.full_name = filtered_lines[0]
    except Exception as e:
        st.error(f"OCR Error processing NRIC: {e}. Please enter details manually.")

# ==========================================
# 2) TAKE / UPLOAD PHOTO OF BANK DETAILS
# ==========================================
st.markdown("### 2️⃣ Bank Account Extraction / 銀行户口资料")
bank_source = st.radio("Choose Bank Document Source:", ("Camera / Take Photo", "Upload File"), horizontal=True, key="bank_src")

bank_image = None
if bank_source == "Camera / Take Photo":
    bank_image = st.camera_input("Capture Bank Statement Header / Passbook", key="bank_cam")
else:
    bank_image = st.file_uploader("Upload Bank Document Image", type=["jpg", "jpeg", "png"], key="bank_upload")

if bank_image is not None:
    try:
        img_bank = Image.open(bank_image)
        img_bank_np = np.array(img_bank)
        with st.spinner("Extracting bank details..."):
            results_bank = reader.readtext(img_bank_np, detail=0)
            extracted_bank_text = " ".join(results_bank).upper()
            
            common_banks = ["DBS", "POSB", "OCBC", "UOB", "HSBC", "STANDARD CHARTERED", "CITIBANK"]
            for bank in common_banks:
                if bank in extracted_bank_text:
                    st.session_state.bank_name = bank
                    break
            
            acc_match = re.search(r'\b\d{3}[-\s]?\d{3,4}[-\s]?\d{3,4}\b|\b\d{7,12}\b', extracted_bank_text)
            if acc_match:
                st.session_state.bank_acc = acc_match.group(0).replace(" ", "").replace("-", "")
                st.success("✓ Automatically extracted Bank Account information!")
    except Exception as e:
        st.error(f"OCR Error processing Bank Statement: {e}. Please enter details manually.")

st.markdown("---")

# ==========================================
# APPLICATION FORM INPUT FIELDS
# ==========================================
st.markdown("### 📋 Application Details / 申请者资料 Fill-in")

with st.form("application_form"):
    full_name = st.text_input("Full Name as in NRIC/Passport / 身份证/护照上的全名", value=st.session_state.full_name)
    nric_no = st.text_input("NRIC No / 身份证号码", value=st.session_state.nric_no)
    
    col1, col2 = st.columns(2)
    with col1:
        bank_name = st.text_input("Bank Name / 銀行名稱", value=st.session_state.bank_name)
    with col2:
        bank_account = st.text_input("Bank Account No / 銀行户口号码", value=st.session_state.bank_acc)

    current_date_str = datetime.today().strftime('%Y-%m-%d')
    date_stamp = st.text_input("Date / 日期 (Auto Date-Stamped)", value=current_date_str, disabled=True)

    st.markdown("---")
    
    st.markdown("### 3️⃣ Signature / 签名")
    st.write("Please sign inside the box below:")
    
    canvas_result = st_canvas(
        fill_color="rgba(255, 255, 255, 1)",
        stroke_width=3,
        stroke_color="#111111",
        background_color="#f9fafb",
        height=150,
        width=400,
        drawing_mode="freedraw",
        key="signature",
    )

    submitted = st.form_submit_button("VALIDATE & GENERATE DOWNLOAD")

if submitted:
    if not full_name or not nric_no or not bank_account:
        st.error("Please ensure all fields are filled out.")
    elif canvas_result.image_data is None or len(canvas_result.json_data["objects"]) == 0:
        st.error("Please provide your E-signature before downloading.")
    else:
        st.success("🎉 Verification Complete! Your download file is ready below.")

        sig_image = Image.fromarray(canvas_result.image_data.astype('uint8'), 'RGBA')
        sig_buffer = io.BytesIO()
        sig_image.save(sig_buffer, format="PNG")
        sig_buffer.seek(0)

        pdf_buffer = io.BytesIO()
        doc = SimpleDocTemplate(pdf_buffer, pagesize=letter, rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40)
        story = []

        title_style = ParagraphStyle(name='TitleStyle', fontName='Helvetica-Bold', fontSize=18, textColor=colors.HexColor("#78350f"), alignment=1)
        subtitle_style = ParagraphStyle(name='SubTitleStyle', fontName='Helvetica', fontSize=9, textColor=colors.gray, alignment=1)
        label_style = ParagraphStyle(name='LabelStyle', fontName='Helvetica-Bold', fontSize=10, textColor=colors.HexColor("#1f2937"))
        value_style = ParagraphStyle(name='ValueStyle', fontName='Helvetica', fontSize=11, textColor=colors.black)

        story.append(Paragraph("NIRVANA MEMORIAL GARDEN PTE. LTD.", title_style))
        story.append(Paragraph("SERVICE ADVISOR APPLICATION FORM (NV-SG-CSD-F01 Rev.2)", subtitle_style))
        story.append(Spacer(1, 25))

        # Using clean_pdf_text to protect Helvetica against non-latin character errors
        data = [
            [Paragraph("Full Name as in NRIC / Passport:", label_style), Paragraph(clean_pdf_text(full_name), value_style)],
            [Paragraph("NRIC / Passport No:", label_style), Paragraph(clean_pdf_text(nric_no), value_style)],
            [Paragraph("Bank Account Provider Name:", label_style), Paragraph(clean_pdf_text(bank_name), value_style)],
            [Paragraph("Bank Account Number:", label_style), Paragraph(clean_pdf_text(bank_account), value_style)],
            [Paragraph("Application Date (Stamped):", label_style), Paragraph(clean_pdf_text(date_stamp), value_style)]
        ]

        t = Table(data, colWidths=[200, 300])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (0,-1), colors.HexColor("#f9fafb")),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#e5e7eb")),
            ('PADDING', (0,0), (-1,-1), 10),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ]))
        story.append(t)
        story.append(Spacer(1, 30))

        story.append(Paragraph("Applicant Signature / Authorization Stamp:", label_style))
        story.append(Spacer(1, 5))
        rl_sig_img = RLImage(sig_buffer, width=200, height=75)
        rl_sig_img.hAlign = 'LEFT'
        story.append(rl_sig_img)

        doc.build(story)
        pdf_data = pdf_buffer.getvalue()

        st.download_button(
            label="📥 Download Completed PDF Form",
            data=pdf_data,
            file_name=f"Signed_NV-SG-CSD-F01_{nric_no}.pdf",
            mime="application/pdf"
        )
