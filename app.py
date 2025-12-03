import streamlit as st
import fitz  # PyMuPDF
import io
from PIL import Image

# --- 1. CONFIGURATION ---
st.set_page_config(
    page_title="DocPolish",
    page_icon=None,
    layout="wide"
)

# --- 2. PROFESSIONAL CSS ---
st.markdown("""
    <style>
    /* IMPORT FONTS */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
    
    /* 1. LAYOUT RESET */
    .block-container {
        padding-top: 2rem !important;
        padding-bottom: 3rem !important;
        max-width: 1100px !important;
        margin: 0 auto !important;
    }
    
    /* 2. UI CLEANUP */
    [data-testid="stHeader"] { display: none !important; }
    #MainMenu, footer { visibility: hidden; }
    [data-testid="stAppViewContainer"] { background-color: #FFFFFF !important; }
    
    /* 3. TYPOGRAPHY */
    * { font-family: 'Inter', sans-serif !important; color: #111111; }

    .hero-title {
        font-weight: 800;
        background: -webkit-linear-gradient(45deg, #820AD1, #B220E8);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 3rem;
        text-align: center;
        margin-bottom: 10px;
        letter-spacing: -0.02em;
    }
    .hero-subtitle {
        color: #6B7280;
        font-size: 1.1rem;
        text-align: center;
        margin-bottom: 40px;
        font-weight: 400;
        letter-spacing: -0.01em;
    }

    /* 4. UPLOAD BOX (Professional & Compact) */
    [data-testid="stFileUploader"] {
        background-color: #FAFAFA;
        border: 1px dashed #D1D5DB; /* Thinner, gray border */
        border-radius: 12px;
        padding: 30px;
        text-align: center;
    }
    [data-testid="stFileUploader"]:hover {
        border-color: #820AD1;
        background-color: #FDFBFF;
    }

    /* 5. DOWNLOAD BUTTON */
    .stDownloadButton > button {
        background-color: #111111 !important; /* Solid Black for Professionalism */
        color: white !important;
        border-radius: 8px;
        padding: 0.8rem 2rem;
        font-weight: 600;
        width: 100%;
        border: none;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        transition: all 0.2s;
    }
    .stDownloadButton > button:hover {
        background-color: #252525 !important;
        transform: translateY(-1px);
        box-shadow: 0 6px 15px -3px rgba(0, 0, 0, 0.15);
    }
    
    /* 6. PREVIEW IMAGE */
    img {
        border: 1px solid #E5E7EB;
        border-radius: 8px;
        box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05);
    }
    
    /* 7. PAGE COUNT BADGE */
    .page-badge {
        background-color: #FFFFFF;
        color: #6B7280;
        padding: 6px 16px;
        border-radius: 6px;
        font-size: 0.85rem;
        font-weight: 500;
        display: inline-block;
        margin-top: 10px;
        border: 1px solid #E5E7EB;
    }
    
    /* 8. INPUTS (Clean) */
    .stTextInput input {
        border: 1px solid #E5E7EB;
        border-radius: 6px;
        padding: 10px;
    }
    
    /* Feature Cards (No Icons) */
    .feature-card {
        background: #FFFFFF;
        padding: 25px 20px;
        border-radius: 12px;
        border: 1px solid #E5E7EB;
        text-align: center;
        height: 100%;
        transition: border-color 0.2s;
    }
    .feature-card:hover {
        border-color: #820AD1;
    }
    .feature-title { font-weight: 700; font-size: 1rem; margin-bottom: 8px; color: #111; }
    .feature-text { color: #666; font-size: 0.9rem; line-height: 1.5; }
    
    /* Section Headers */
    h3 { font-size: 1rem !important; font-weight: 700 !important; color: #374151 !important; margin-bottom: 10px !important; }
    </style>
""", unsafe_allow_html=True)

# --- 3. LOGIC ---

def clean_page_logic(page, header_h, footer_h, text_input, match_case):
    if text_input:
        keywords = [k.strip() for k in text_input.split(',')]
        for keyword in keywords:
            if not keyword: continue
            quads = page.search_for(keyword)
            for quad in quads:
                if match_case:
                    res = page.get_text("text", clip=quad).strip()
                    if keyword not in res: continue
                page.add_redact_annot(quad, fill=None)
        page.apply_redactions()

    rect = page.rect
    # Smart color detection
    clip = fitz.Rect(0, rect.height-10, 1, rect.height-9)
    pix = page.get_pixmap(clip=clip)
    r, g, b = pix.pixel(0, 0)
    dynamic_color = (r/255, g/255, b/255)

    if footer_h > 0:
        page.draw_rect(fitz.Rect(0, rect.height - footer_h, rect.width, rect.height), color=dynamic_color, fill=dynamic_color)
    if header_h > 0:
        page.draw_rect(fitz.Rect(0, 0, rect.width, header_h), color=dynamic_color, fill=dynamic_color)

def get_pdf_info(file_bytes):
    doc = fitz.open(stream=file_bytes, filetype="pdf")
    return len(doc)

@st.cache_data(show_spinner=False)
def get_preview_image(file_bytes, header_h, footer_h, txt, case):
    doc = fitz.open(stream=file_bytes, filetype="pdf")
    if len(doc) < 1: return None
    page = doc[0]
    clean_page_logic(page, header_h, footer_h, txt, case)
    pix = page.get_pixmap(dpi=120) 
    return Image.open(io.BytesIO(pix.tobytes("png")))

@st.cache_data
def process_full_document(file_bytes, header_h, footer_h, txt, case):
    doc = fitz.open(stream=file_bytes, filetype="pdf")
    output_buffer = io.BytesIO()
    doc.set_metadata({}) 
    for page in doc:
        clean_page_logic(page, header_h, footer_h, txt, case)
    doc.save(output_buffer)
    output_buffer.seek(0)
    return output_buffer

# --- 4. UI LAYOUT ---

# Header
st.markdown('<div class="hero-title">DocPolish</div>', unsafe_allow_html=True)
st.markdown('<div class="hero-subtitle">Professional Document Remediation</div>', unsafe_allow_html=True)

# UPLOAD SECTION (Compact Width: 1-1.5-1 ratio)
c_up1, c_up2, c_up3 = st.columns([1, 1.5, 1])
with c_up2:
    uploaded_file = st.file_uploader("Upload PDF", type="pdf", label_visibility="collapsed")
    
    # Page Count Badge (Subtle)
    if uploaded_file:
        page_count = get_pdf_info(uploaded_file.getvalue())
        st.markdown(f'<div style="text-align: center;"><span class="page-badge">{page_count} Pages Detected</span></div>', unsafe_allow_html=True)

# --- STATE 1: NO FILE ---
if not uploaded_file:
    st.write("")
    st.write("")
    c1, c2, c3 = st.columns(3, gap="medium")
    with c1:
        st.markdown("""<div class="feature-card"><div class="feature-title">Text Eraser</div><div class="feature-text">Automatically detects and removes specific words or sensitive phrases from every page.</div></div>""", unsafe_allow_html=True)
    with c2:
        st.markdown("""<div class="feature-card"><div class="feature-title">Area Masking</div><div class="feature-text">Clean headers, footers, and margins with precise pixel-level control.</div></div>""", unsafe_allow_html=True)
    with c3:
        st.markdown("""<div class="feature-card"><div class="feature-title">Secure Processing</div><div class="feature-text">All operations run locally in your browser session. No data is stored.</div></div>""", unsafe_allow_html=True)

# --- STATE 2: WORKSPACE ---
else:
    st.write("---")

    # MAIN STUDIO (Left Controls | Right Preview)
    col_left, col_right = st.columns([1, 1], gap="large")

    with col_left:
        st.markdown("### Text Eraser")
        text_input = st.text_input("keywords", placeholder="e.g. Confidential, Draft", label_visibility="collapsed")
        match_case = st.checkbox("Match Case", value=False)
        st.caption("Removes exact matches of words or phrases.")
        
        st.write("") 
        
        st.markdown("### Area Masking")
        
        st.caption("Header Height")
        header_height = st.slider("Header", 0, 150, 0, label_visibility="collapsed")
        
        st.caption("Footer Height")
        footer_height = st.slider("Footer", 0, 150, 0, label_visibility="collapsed")

    with col_right:
        st.markdown("### Live Preview")
        preview_img = get_preview_image(uploaded_file.getvalue(), header_height, footer_height, text_input, match_case)
        if preview_img:
            # RESTRICTED WIDTH (Matches left column weight)
            st.image(preview_img, width=350)

    # ACTION AREA
    st.write("---")
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        final_pdf_data = process_full_document(
            uploaded_file.getvalue(), 
            header_height, 
            footer_height, 
            text_input, 
            match_case
        )
        st.download_button(
            label="Download Clean PDF",
            data=final_pdf_data,
            file_name=f"Clean_{uploaded_file.name}",
            mime="application/pdf"
        )
