import streamlit as st
import easyocr
import numpy as np
from PIL import Image
import re
import io
from datetime import datetime
from streamlit_drawable_canvas import st_canvas

# PDF overlay imports
from pypdf import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.utils import ImageReader  # Added to wrap BytesIO properly

# Set page configuration
st.set_page_config(page_title="Nirvana Service Advisor Onboarding", layout="centered")

# Initialize EasyOCR Reader
@st.cache_resource
def load_ocr():
    return easyocr.Reader(['en'])

reader = load_ocr()

# --- APP HEADER ---
st.title("富貴 NIRVANA")
st.subheader("SERVICE ADVISOR APPLICATION FORM / 代理商申请表格")
st.caption("Template Reference: (ISO FORM) NV-SG-CSD-F01 Rev.2 Service Advisor Application Form - with effect 01.05.2023.pdf")

st.markdown("---")

# Initialize Session States for OCR Extraction
if "full_name" not in st.session_state: st.session_state.full_name = ""
if "nric_no" not in st.session_state: st.session_state.nric_no = ""
if "bank_name" not in st.session_state: st.session_state.bank_name = ""
if "bank_acc" not in st.session_state: st.session_state.bank_acc = ""

# ==========================================
# AUTOMATED OCR SECTION
# ==========================================
st.markdown("### 📷 Smart Extraction / 智能资料提取 (Optional)")
col_ocr1, col_ocr2 = st.columns(2)

with col_ocr1:
    ic_image = st.file_uploader("Upload NRIC Image (Front)", type=["jpg", "jpeg", "png"])
    if ic_image is not None:
        try:
            img = Image.open(ic_image)
            with st.spinner("Extracting NRIC..."):
                results = reader.readtext(np.array(img), detail=0)
                extracted_text = " ".join(results)
                nric_match = re.search(r'[STFGM]\d{7}[A-Z]', extracted_text, re.IGNORECASE)
                if nric_match:
                    st.session_state.nric_no = nric_match.group(0).upper()
                lines = [line.strip().upper() for line in results if len(line.strip()) > 3]
                filtered = [l for l in lines if not any(x in l for x in ["IDENTITY", "CARD", "SINGAPORE", "REPUBLIC"])]
                if filtered:
                    st.session_state.full_name = filtered[0]
            st.success("✓ NRIC read successfully!")
        except Exception as e:
            st.error(f"OCR Error: {e}")

with col_ocr2:
    bank_image = st.file_uploader("Upload Bank Document Header", type=["jpg", "jpeg", "png"])
    if bank_image is not None:
        try:
            img_bank = Image.open(bank_image)
            with st.spinner("Extracting Bank Details..."):
                results_bank = reader.readtext(np.array(img_bank), detail=0)
                extracted_bank_text = " ".join(results_bank).upper()
                common_banks = ["DBS", "POSB", "OCBC", "UOB", "HSBC", "STANDARD CHARTERED", "CITIBANK"]
                for bank in common_banks:
                    if bank in extracted_bank_text:
                        st.session_state.bank_name = bank
                        break
                acc_match = re.search(r'\b\d{3}[-\s]?\d{3,4}[-\s]?\d{3,4}\b|\b\d{7,12}\b', extracted_bank_text)
                if acc_match:
                    st.session_state.bank_acc = acc_match.group(0).replace(" ", "").replace("-", "")
            st.success("✓ Bank details read successfully!")
        except Exception as e:
            st.error(f"OCR Error: {e}")

st.markdown("---")

# ==========================================
# INTERACTIVE APPLICATION FORM
# ==========================================
st.markdown("## 📋 INTERACTIVE APPLICATION FORM")

with st.form("official_nirvana_form"):
    
    st.markdown("#### 👤 PART 1: PARTICULARS OF RECRUITING SERVICE ADVISOR (UPLINE)")
    upline_name = st.text_input("Upline Name / 上线姓名", value="Milk")
    col_u1, col_u2 = st.columns(2)
    with col_u1:
        upline_nric = st.text_input("Upline NRIC No / 上线身份证号码", value="S76545677A")
    with col_u2:
        upline_code = st.text_input("Agency & Advisor Code / 区代理及代理商号码", value="763")
        
    st.markdown("---")
    
    st.markdown("#### 👤 PART 2: PARTICULARS OF APPLICANT")
    full_name = st.text_input("Full Name (as in NRIC/Passport)", value=st.session_state.full_name if st.session_state.full_name else "S6971518D")
    id_display_name = st.text_input("Name to Display on ID Card", value="Jack")
    
    col_a1, col_a2 = st.columns(2)
    with col_a1:
        nric_no = st.text_input("NRIC No / Passport No", value=st.session_state.nric_no if st.session_state.nric_no else "S6971518D")
        dob = st.text_input("Date Of Birth (YYYY-MM-DD)", value="1990-01-01")
        sex = st.text_input("Sex (MALE/FEMALE)", value="MALE")
        marital = st.text_input("Marital Status (Single/Married)", value="Single")
    with col_a2:
        nationality = st.text_input("Nationality", value="Singaporean")
        mobile_no = st.text_input("Mobile Telephone", value="9888256")
        home_no = st.text_input("Home Telephone", value="")
        email_addr = st.text_input("E-Mail Address", value="")
        
    address = st.text_area("Correspondence Address")
    
    col_b1, col_b2 = st.columns(2)
    with col_b1:
        bank_name = st.text_input("Bank Name", value=st.session_state.bank_name if st.session_state.bank_name else "POSB")
    with col_b2:
        bank_account = st.text_input("Bank Account Number", value=st.session_state.bank_acc if st.session_state.bank_acc else "120481254")
        
    social_1 = st.text_input("Social Handle 1")
    social_2 = st.text_input("Social Handle 2")

    st.markdown("---")

    st.markdown("#### 🚨 PART 3: EMERGENCY CONTACT PARTICULARS")
    col_e1, col_e2, col_e3 = st.columns(3)
    with col_e1:
        emerg_name = st.text_input("Contact Person Name", value="Jack")
    with col_e2:
        emerg_phone = st.text_input("Contact Telephone No", value="9288356")
    with col_e3:
        emerg_relat = st.text_input("Relationship", value="Spouse")

    st.markdown("---")

    st.markdown("#### ℹ️ PART 4: BACKGROUND QUESTIONS & CHARACTER REFERENCE")
    convicted = st.text_input("Criminal Violation History? (YES/NO)", value="NO")
    bankrupt = st.text_input("Declared Bankrupt History? (YES/NO)", value="NO")
    
    col_r1, col_r2 = st.columns(2)
    with col_r1:
        ref_name = st.text_input("Reference Full Name", value="Mini")
        ref_company = st.text_input("Company Name & Job", value="Fkall")
    with col_r2:
        ref_relat = st.text_input("Relationship Status", value="Friends")
        ref_phone = st.text_input("Telephone Contact", value="98888188")

    st.markdown("---")
    
    st.markdown("#### ✍️ PART 5: APPLICANT COMPLIANCE EXECUTION DECLARATION")
    canvas_result = st_canvas(
        fill_color="rgba(255, 255, 255, 1)",
        stroke_width=3,
        stroke_color="#111111",
        background_color="#f9fafb",
        height=120,
        width=400,
        drawing_mode="freedraw",
        key="signature",
    )
    
    current_date_str = datetime.today().strftime('%Y-%m-%d')
    submitted = st.form_submit_button("STAMP & GENERATE OFFICIAL OVERLAY PDF")

# ==========================================
# THE OVERLAY MERGE ENGINE
# ==========================================
if submitted:
    if canvas_result.image_data is None or len(canvas_result.json_data["objects"]) == 0:
        st.error("❌ Signature Error: Please complete your signature block.")
    else:
        try:
            # 1. Process Signature Image
            sig_image = Image.fromarray(canvas_result.image_data.astype('uint8'), 'RGBA')
            sig_buffer = io.BytesIO()
            sig_image.save(sig_buffer, format="PNG")
            sig_buffer.seek(0)

            # Wrap BytesIO in an ImageReader instance for ReportLab canvas
            reportlab_io_img = ImageReader(sig_buffer)

            # 2. Draw standard form inputs onto a transparent temporary ReportLab PDF
            packet = io.BytesIO()
            can = canvas.Canvas(packet, pagesize=letter)
            can.setFont("Helvetica", 9)

            # Coordinates mapping table
            can.drawString(110, 688, upline_name)
            can.drawString(410, 688, upline_nric)
            can.drawString(110, 668, upline_code)

            can.drawString(130, 625, full_name)
            can.drawString(410, 625, id_display_name)
            can.drawString(110, 604, nric_no)
            can.drawString(410, 604, dob)
            can.drawString(110, 587, sex)
            can.drawString(410, 587, nationality)
            can.drawString(110, 570, marital)
            can.drawString(410, 570, email_addr)
            can.drawString(110, 554, mobile_no)
            can.drawString(410, 554, home_no)
            can.drawString(130, 537, address)
            can.drawString(110, 510, bank_name)
            can.drawString(410, 510, bank_account)
            can.drawString(110, 492, social_1)
            can.drawString(410, 492, social_2)

            can.drawString(110, 448, emerg_name)
            can.drawString(410, 448, emerg_relat)
            can.drawString(110, 431, emerg_phone)

            can.drawString(130, 390, convicted)
            can.drawString(410, 390, bankrupt)
            can.drawString(110, 373, ref_name)
            can.drawString(410, 373, ref_relat)
            can.drawString(110, 356, ref_company)
            can.drawString(410, 356, ref_phone)
            
            can.drawString(410, 260, current_date_str)

            # Draw Signature Image using ImageReader wrapper
            can.drawImage(reportlab_io_img, 60, 180, width=120, height=50, mask='auto')
            
            can.save()
            packet.seek(0)

            # 3. Read background original template file and stamp the dynamic input layer on top
            template_filename = "(ISO FORM) NV-SG-CSD-F01 Rev.2 Service Advisor Application Form - with effect 01.05.2023.pdf"
            
            existing_pdf = PdfReader(open(template_filename, "rb"))
            new_pdf = PdfReader(packet)
            output = PdfWriter()

            # Merge page 1 data strings layer onto template page 1
            page = existing_pdf.pages[0]
            page.merge_page(new_pdf.pages[0])
            output.add_page(page)

            # Append remainder pages intact if document has more pages
            for i in range(1, len(existing_pdf.pages)):
                output.add_page(existing_pdf.pages[i])

            # 4. Stream final merged result out to dynamic user download button
            final_buffer = io.BytesIO()
            output.write(final_buffer)
            final_pdf_data = final_buffer.getvalue()

            st.success("🎉 Seamless Template Form Generated!")
            st.download_button(
                label="📥 Download Official Stamped Form PDF",
                data=final_pdf_data,
                file_name=f"Official_NV-SG-CSD-F01_{nric_no}.pdf",
                mime="application/pdf"
            )
        except FileNotFoundError:
            st.error("❌ Base Template Error: Please verify that you uploaded '(ISO FORM) NV-SG-CSD-F01 Rev.2 Service Advisor Application Form - with effect 01.05.2023.pdf' to your root directory.")
        except Exception as e:
            st.error(f"Error compiling form template stack: {e}")
