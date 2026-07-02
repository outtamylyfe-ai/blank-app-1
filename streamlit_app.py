import streamlit as st
import easyocr
import numpy as np
from PIL import Image
import re
import io
from datetime import datetime
from streamlit_drawable_canvas import st_canvas

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
    return re.sub(r'[^\x00-\x7F]+', '', str(text)).strip()

# Initialize EasyOCR Reader
@st.cache_resource
def load_ocr():
    return easyocr.Reader(['en'])

reader = load_ocr()

# --- APP HEADER ---
st.title("富貴 NIRVANA")
st.subheader("SERVICE ADVISOR APPLICATION FORM / 代理商申请表格")
st.caption("Form Ref: NV-SG-CSD-F01 Rev.2")

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
# 📋 THE OFFICIAL FULL APPLICATION FORM
# ==========================================
st.markdown("## 📋 INTERACTIVE APPLICATION FORM")

with st.form("official_nirvana_form"):
    
    # 1. PARTICULARS OF RECRUITING SERVICE ADVISOR (UPLINE)
    st.markdown("#### 👤 PART 1: PARTICULARS OF RECRUITING SERVICE ADVISOR (UPLINE) / 推荐代理商(上线)资料")
    upline_name = st.text_input("Upline Name / 上线姓名")
    col_u1, col_u2 = st.columns(2)
    with col_u1:
        upline_nric = st.text_input("Upline NRIC No / 上线身份证号码")
    with col_u2:
        upline_code = st.text_input("Agency & Advisor Code / 区代理及代理商号码")
        
    st.markdown("---")
    
    # 2. PARTICULARS OF APPLICANT
    st.markdown("#### 👤 PART 2: PARTICULARS OF APPLICANT / 申请者资料")
    full_name = st.text_input("Full Name (as in NRIC/Passport) / 身份证/护照上的全名", value=st.session_state.full_name)
    id_display_name = st.text_input("Name to Display on ID Card / 卡片显示名")
    
    col_a1, col_a2 = st.columns(2)
    with col_a1:
        nric_no = st.text_input("NRIC No / 身份证号码", value=st.session_state.nric_no)
        dob = st.text_input("Date Of Birth / 出生日期 (YYYY-MM-DD)")
        sex = st.radio("Sex / 性別", ["MALE 男", "FEMALE 女"], horizontal=True)
        marital = st.radio("Marital Status / 婚姻狀況", ["Single 单身", "Married 已婚", "Others 其它"], horizontal=True)
    with col_a2:
        nationality = st.text_input("Nationality / 国籍")
        mobile_no = st.text_input("Mobile No / 手提")
        home_no = st.text_input("Home No / 住家")
        email_addr = st.text_input("E-Mail Address / 电子邮件地址")
        
    address = st.text_area("Correspondence Address / 通讯地址")
    
    col_b1, col_b2 = st.columns(2)
    with col_b1:
        bank_name = st.text_input("Bank Name / 銀行名稱", value=st.session_state.bank_name)
    with col_b2:
        bank_account = st.text_input("Bank Account No / 銀行户口号码", value=st.session_state.bank_acc)
        
    social_1 = st.text_input("Social Handle 1 / 社交媒体账号")
    social_2 = st.text_input("Social Handle 2 / 社交媒体账号")

    st.markdown("---")

    # 3. EMERGENCY CONTACT
    st.markdown("#### 🚨 PART 3: EMERGENCY CONTACT / 紧急连联络号码")
    col_e1, col_e2, col_e3 = st.columns(3)
    with col_e1:
        emerg_name = st.text_input("Emergency Contact Name / 姓名")
    with col_e2:
        emerg_phone = st.text_input("Contact No / 联络号码")
    with col_e3:
        emerg_relat = st.text_input("Relationship / 关系")

    st.markdown("---")

    # 4. OTHER INFORMATIONS
    st.markdown("#### ℹ️ PART 4: OTHERS INFORMATIONS / 其他资料")
    convicted = st.radio("Have you and/or your spouse ever been convicted of any violation of criminal law before? / 您或你的配偶之前,有任何违反刑法或被定罪吗?", ["NO 沒有", "YES 有"], horizontal=True)
    bankrupt = st.radio("Have you ever been bankrupt before? / 您是否曾是破产者?", ["NO 沒有", "YES 有"], horizontal=True)
    
    st.write("**Reference (Non-relative) / 推荐人资料:**")
    col_r1, col_r2 = st.columns(2)
    with col_r1:
        ref_name = st.text_input("Reference Name / 姓名")
        ref_company = st.text_input("Company Name & Occupation / 公司 & 职业")
    with col_r2:
        ref_relat = st.text_input("Relationship with Service Advisor / 与代理的关系")
        ref_phone = st.text_input("Telephone / 电话")

    st.markdown("---")
    
    # 5. SIGNATURE DECLARATION
    st.markdown("#### ✍️ PART 5: DECLARATION & SIGNATURE / 宣告与签名")
    st.caption("By signing, you acknowledge you have read, understood and agree to the Nirvana Code of Ethics and Privacy Policies.")
    
    canvas_result = st_canvas(
        fill_color="rgba(255, 255, 255, 1)",
        stroke_width=3,
        stroke_color="#111111",
        background_color="#f9fafb",
        height=150,
        width=450,
        drawing_mode="freedraw",
        key="signature",
    )
    
    current_date_str = datetime.today().strftime('%Y-%m-%d')
    st.text_input("Application Date / 日期", value=current_date_str, disabled=True)

    submitted = st.form_submit_button("VALIDATE & GENERATE OFFICIAL FORM PDF")

# ==========================================
# REPORTLAB PDF GENERATION ENGINE
# ==========================================
if submitted:
    if not full_name or not nric_no or not bank_account:
        st.error("❌ Mandatory Field Error: Please fill up Applicant Name, NRIC, and Bank Account details.")
    elif canvas_result.image_data is None or len(canvas_result.json_data["objects"]) == 0:
        st.error("❌ Signature Error: Please complete your E-signature box before generating.")
    else:
        st.success("🎉 Forms Validated! Ready to download your official structural document.")

        # Save signature canvas stream
        sig_image = Image.fromarray(canvas_result.image_data.astype('uint8'), 'RGBA')
        sig_buffer = io.BytesIO()
        sig_image.save(sig_buffer, format="PNG")
        sig_buffer.seek(0)

        # Initialize PDF Document Architecture
        pdf_buffer = io.BytesIO()
        doc = SimpleDocTemplate(pdf_buffer, pagesize=letter, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30)
        story = []

        # Style Sheets
        title_style = ParagraphStyle('T1', fontName='Helvetica-Bold', fontSize=14, textColor=colors.HexColor("#78350f"), alignment=1)
        sub_style = ParagraphStyle('T2', fontName='Helvetica-Bold', fontSize=11, alignment=1)
        meta_style = ParagraphStyle('T3', fontName='Helvetica', fontSize=8, textColor=colors.gray, alignment=1)
        
        section_heading = ParagraphStyle('SH', fontName='Helvetica-Bold', fontSize=9, textColor=colors.white, backColor=colors.HexColor("#1e3a8a"), borderPadding=4)
        label_style = ParagraphStyle('L', fontName='Helvetica-Bold', fontSize=8, textColor=colors.HexColor("#1f2937"))
        val_style = ParagraphStyle('V', fontName='Helvetica', fontSize=8, textColor=colors.black)

        # Header Structure
        story.append(Paragraph("NIRVANA MEMORIAL GARDEN PTE. LTD.", title_style))
        story.append(Paragraph("SERVICE ADVISOR APPLICATION FORM", sub_style))
        story.append(Paragraph("Form ID: NV-SG-CSD-F01 | A Member of Nirvana Asia Group", meta_style))
        story.append(Spacer(1, 15))

        # --- TABLE 1: UPLINE INFO ---
        story.append(Paragraph("PARTICULARS OF RECRUITING SERVICE ADVISOR (UPLINE)", section_heading))
        story.append(Spacer(1, 4))
        upline_data = [
            [Paragraph("Upline Name:", label_style), Paragraph(clean_pdf_text(upline_name), val_style), Paragraph("Upline NRIC:", label_style), Paragraph(clean_pdf_text(upline_nric), val_style)],
            [Paragraph("Agency & Advisor Code:", label_style), Paragraph(clean_pdf_text(upline_code), val_style), "", ""]
        ]
        t_upline = Table(upline_data, colWidths=[120, 155, 100, 175])
        t_upline.setStyle(TableStyle([('GRID', (0,0), (-1,-1), 0.5, colors.lightgrey), ('VALIGN', (0,0), (-1,-1), 'MIDDLE'), ('SPAN', (1,1), (3,1))]))
        story.append(t_upline)
        story.append(Spacer(1, 12))

        # --- TABLE 2: APPLICANT PARTICULARS ---
        story.append(Paragraph("PARTICULARS OF APPLICANT", section_heading))
        story.append(Spacer(1, 4))
        applicant_data = [
            [Paragraph("Full Name (NRIC/Passport):", label_style), Paragraph(clean_pdf_text(full_name), val_style), Paragraph("Display Name (ID Card):", label_style), Paragraph(clean_pdf_text(id_display_name), val_style)],
            [Paragraph("NRIC / Passport No:", label_style), Paragraph(clean_pdf_text(nric_no), val_style), Paragraph("Date Of Birth:", label_style), Paragraph(clean_pdf_text(dob), val_style)],
            [Paragraph("Sex:", label_style), Paragraph(clean_pdf_text(sex), val_style), Paragraph("Nationality:", label_style), Paragraph(clean_pdf_text(nationality), val_style)],
            [Paragraph("Marital Status:", label_style), Paragraph(clean_pdf_text(marital), val_style), Paragraph("E-Mail Address:", label_style), Paragraph(clean_pdf_text(email_addr), val_style)],
            [Paragraph("Mobile Telephone:", label_style), Paragraph(clean_pdf_text(mobile_no), val_style), Paragraph("Home Telephone:", label_style), Paragraph(clean_pdf_text(home_no), val_style)],
            [Paragraph("Correspondence Address:", label_style), Paragraph(clean_pdf_text(address), val_style), "", ""],
            [Paragraph("Bank Name:", label_style), Paragraph(clean_pdf_text(bank_name), val_style), Paragraph("Bank Account Number:", label_style), Paragraph(clean_pdf_text(bank_account), val_style)],
            [Paragraph("Social Handle 1:", label_style), Paragraph(clean_pdf_text(social_1), val_style), Paragraph("Social Handle 2:", label_style), Paragraph(clean_pdf_text(social_2), val_style)]
        ]
        t_applicant = Table(applicant_data, colWidths=[120, 155, 100, 175])
        t_applicant.setStyle(TableStyle([('GRID', (0,0), (-1,-1), 0.5, colors.lightgrey), ('VALIGN', (0,0), (-1,-1), 'MIDDLE'), ('SPAN', (1,5), (3,5))]))
        story.append(t_applicant)
        story.append(Spacer(1, 12))

        # --- TABLE 3: EMERGENCY CONTACT ---
        story.append(Paragraph("EMERGENCY CONTACT PARTICULARS", section_heading))
        story.append(Spacer(1, 4))
        emerg_data = [
            [Paragraph("Contact Person Name:", label_style), Paragraph(clean_pdf_text(emerg_name), val_style), Paragraph("Relationship:", label_style), Paragraph(clean_pdf_text(emerg_relat), val_style)],
            [Paragraph("Contact Telephone No:", label_style), Paragraph(clean_pdf_text(emerg_phone), val_style), "", ""]
        ]
        t_emerg = Table(emerg_data, colWidths=[120, 155, 100, 175])
        t_emerg.setStyle(TableStyle([('GRID', (0,0), (-1,-1), 0.5, colors.lightgrey), ('VALIGN', (0,0), (-1,-1), 'MIDDLE'), ('SPAN', (1,1), (3,1))]))
        story.append(t_emerg)
        story.append(Spacer(1, 12))

        # --- TABLE 4: OTHER DETAILED QUESTIONS & REFERENCES ---
        story.append(Paragraph("BACKGROUND QUESTIONS & CHARACTER REFERENCE", section_heading))
        story.append(Spacer(1, 4))
        other_data = [
            [Paragraph("Criminal Violation Record History?", label_style), Paragraph(clean_pdf_text(convicted), val_style), Paragraph("Declared Bankrupt History?", label_style), Paragraph(clean_pdf_text(bankrupt), val_style)],
            [Paragraph("Reference Full Name:", label_style), Paragraph(clean_pdf_text(ref_name), val_style), Paragraph("Relationship Status:", label_style), Paragraph(clean_pdf_text(ref_relat), val_style)],
            [Paragraph("Company Name & Job:", label_style), Paragraph(clean_pdf_text(ref_company), val_style), Paragraph("Telephone Contact:", label_style), Paragraph(clean_pdf_text(ref_phone), val_style)]
        ]
        t_other = Table(other_data, colWidths=[120, 155, 100, 175])
        t_other.setStyle(TableStyle([('GRID', (0,0), (-1,-1), 0.5, colors.lightgrey), ('VALIGN', (0,0), (-1,-1), 'MIDDLE')]))
        story.append(t_other)
        story.append(Spacer(1, 15))

        # --- SECTION 5: SIGNATURE & EXECUTION STAMP ---
        story.append(Paragraph("APPLICANT COMPLIANCE EXECUTION DECLARATION", section_heading))
        story.append(Spacer(1, 5))
        story.append(Paragraph("I certify that statements made by me in this application are true, accurate and complete. I declare I have read and will strictly comply with the Nirvana Agency Terms, Conditions and Code of Ethics.", val_style))
        story.append(Spacer(1, 8))
        
        rl_sig_img = RLImage(sig_buffer, width=160, height=60)
        rl_sig_img.hAlign = 'LEFT'
        
        exec_data = [
            [Paragraph("Applicant Signature Authorization Stamp:", label_style), Paragraph(f"Execution Date: {current_date_str}", label_style)],
            [rl_sig_img, ""]
        ]
        t_exec = Table(exec_data, colWidths=[275, 275])
        t_exec.setStyle(TableStyle([('VALIGN', (0,0), (-1,-1), 'TOP')]))
        story.append(t_exec)

        # Build Document
        doc.build(story)
        pdf_data = pdf_buffer.getvalue()

        # Download trigger layout
        st.download_button(
            label="📥 Download Completed NV-SG-CSD-F01 PDF Form",
            data=pdf_data,
            file_name=f"NV-SG-CSD-F01_{nric_no}.pdf",
            mime="application/pdf"
        )
