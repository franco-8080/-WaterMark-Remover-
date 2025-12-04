import streamlit as st
import fitz  # PyMuPDF
import io
from PIL import Image
from collections import Counter

# --- 1. CONFIGURATION ---
st.set_page_config(
    page_title="PDF Watermark Remover",
    page_icon="💧", 
    layout="wide"
)

# --- 2. CSS STYLING ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    [data-testid="stExpander"] svg, [class*="material-symbols"], .st-emotion-cache-1pbqwg9 { font-family: 'Material Symbols Rounded' !important; }
    [data-testid="stFileUploader"] { background-color: #FFFFFF; border: 2px dashed #E5E7EB; border-radius: 20px; padding: 30px; }
    [data-testid="stFileUploader"]:hover { border-color: #3B82F6; background-color: #EFF6FF; }
    .auto-detect-box { background: linear-gradient(to right, #EFF6FF, #DBEAFE); border: 1px solid #BFDBFE; color: #1E40AF; padding: 12px 20px; border-radius: 12px; margin-bottom: 20px; }
    .hero-container { text-align: center; margin-bottom: 40px; padding: 20px 0; }
    .hero-title { font-weight: 800; background: linear-gradient(135deg, #2563EB 0%, #06B6D4 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-size: 3.5rem; letter-spacing: -1px; margin-bottom: 8px; }
    .hero-subtitle { color: #6B7280; font-size: 1.2rem; font-weight: 400; }
    .stDownloadButton > button { background: linear-gradient(135deg, #2563EB 0%, #06B6D4 100%); color: white !important; border: none; padding: 0.6rem 2rem; border-radius: 10px; font-weight: 600; width: 100%; transition: all 0.3s ease; }
    .stDownloadButton > button:hover { box-shadow: 0 10px 15px -3px rgba(37, 99, 235, 0.4); transform: translateY(-2px); }
    [data-testid="stHeader"], footer { display: none !important; }
    .block-container { padding-top: 2rem !important; }
    div[data-testid="stImage"] { display: flex; justify-content: center; }
    </style>
""", unsafe_allow_html=True)

# --- 3. LOGIC ---

def detect_watermark_candidates(file_bytes):
    try:
        doc = fitz.open(stream=file_bytes, filetype="pdf")
        page_limit = min(5, len(doc))
        text_counts = Counter()
        for i in range(page_limit):
            page = doc[i]
            text_blocks = [b[4].strip() for b in page.get_text("blocks")]
            filtered_blocks = [t for t in text_blocks if len(t) > 3]
            text_counts.update(filtered_blocks)
        threshold = max(2, page_limit - 1)
        return ", ".join([text for text, count in text_counts.items() if count >= threshold])
    except Exception:
        return ""

def clean_page_logic(page, header_h, footer_h, keywords_str, match_case):
    # 1. Text Redaction
    if keywords_str:
        keywords = [k.strip() for k in keywords_str.split(',')]
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
    # 2. Smart color detection
    clip = fitz.Rect(0, rect.height-10, 1, rect.height-9)
    pix = page.get_pixmap(clip=clip)
    r, g, b = pix.pixel(0, 0)
    dynamic_color = (r/255, g/255, b/255)

    # 3. Area Wiping
    if footer_h > 0:
        page.draw_rect(fitz.Rect(0, rect.height - footer_h, rect.width, rect.height), color=dynamic_color, fill=dynamic_color)
    if header_h > 0:
        page.draw_rect(fitz.Rect(0, 0, rect.width, header_h), color=dynamic_color, fill=dynamic_color)

@st.cache_data(show_spinner=False)
def get_preview_image(file_bytes, header_h, footer_h, txt, case):
    doc = fitz.open(stream=file_bytes, filetype="pdf")
    if len(doc) < 1: return None
    page = doc[0]
    clean_page_logic(page, header_h, footer_h, txt, case)
    pix = page.get_pixmap(dpi=150) 
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

st.markdown("""
<div class="hero-container">
    <div class="hero-title">PDF Watermark Remover</div>
    <div class="hero-subtitle">Clean, Professional, and Private Document Processing</div>
</div>
""", unsafe_allow_html=True)

# 1. FILE UPLOADER
c1, c2, c3 = st.columns([1, 6, 1])
with c2:
    uploaded_file = st.file_uploader("Drop your PDF here to start", type="pdf", label_visibility="collapsed", key="uploaded_pdf")

# 2. ROBUST CLOUD INITIALIZATION
if uploaded_file:
    file_bytes = uploaded_file.getvalue()
    
    # We use a unique ID based on name and size to track if it's a new file
    # This is safer than .file_id which can vary on Cloud
    current_file_id = f"{uploaded_file.name}_{uploaded_file.size}"
    
    if "active_file_id" not in st.session_state or st.session_state.active_file_id != current_file_id:
        
        # A. SET STATE DEFAULTS PROGRAMMATICALLY
        st.session_state.active_file_id = current_file_id
        st.session_state['footer_slider'] = 25  # Force Footer to 25
        st.session_state['header_slider'] = 0   # Force Header to 0
        
        with st.spinner("🔍 Auto-detecting watermarks..."):
            detected = detect_watermark_candidates(file_bytes)
            st.session_state['text_input_key'] = detected

        # B. FORCE RERUN
        # This is the crucial fix for Streamlit Cloud. 
        # It forces the script to restart immediately so the Sliders pick up the values set above.
        st.rerun()

if not uploaded_file:
    # Landing Page Info
    st.write("")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown('### ⚡ Auto-Detect')
        st.caption("Identifies repetitive text and watermarks automatically.")
    with col2:
        st.markdown('### 🎨 Smart Fill')
        st.caption("Replaces removed areas with matching background color.")
    with col3:
        st.markdown('### 🛡️ Private & Secure')
        st.caption("Files are processed in secure temporary memory.")

else:
    # 3. RENDER UI
    # Notification
    detected_text = st.session_state.get('text_input_key', '')
    if detected_text:
        st.markdown(f"""
        <div class="auto-detect-box">
            🎯 <b>Auto-Detection:</b> Found potential watermarks: <u>{detected_text}</u>
        </div>
        """, unsafe_allow_html=True)

    with st.container(border=True):
        col_settings, col_preview = st.columns([3, 2], gap="large")
        
        with col_settings:
            st.subheader("🛠️ Removal Settings")
            
            # HIDDEN ADVANCED OPTIONS
            with st.expander("Advanced Options", expanded=False):
                st.markdown("**📝 Text Watermarks**")
                # Linked to 'text_input_key' in session state
                text_input = st.text_input(
                    "Keywords", 
                    key="text_input_key", 
                    help="Enter specific words to erase."
                )
                match_case = st.checkbox("Match Case", value=False)
                
                st.markdown("---")
                st.markdown("**✂️ Header & Footer Cutters**")
                
                # SLIDERS (No default 'value=' arg, strictly 'key')
                # They read from st.session_state['header_slider']
                header_height = st.slider(
                    "Top Margin Cut", 0, 150, 
                    key="header_slider",
                    help="White-outs the top X pixels."
                )
                footer_height = st.slider(
                    "Bottom Margin Cut", 0, 150, 
                    key="footer_slider",
                    help="White-outs the bottom X pixels."
                )

            st.write("")
            
            # 4. PROCESSING
            # Uses the slider values which were forced to 25 via session state
            final_pdf_data = process_full_document(
                uploaded_file.getvalue(), 
                header_height, 
                footer_height, 
                text_input, 
                match_case
            )
            
            st.download_button(
                label="📥 Download Clean PDF",
                data=final_pdf_data,
                file_name=f"Clean_{uploaded_file.name}",
                mime="application/pdf"
            )

        with col_preview:
            st.subheader("👁️ Preview")
            # Preview updates immediately because footer_height is 25
            preview_img = get_preview_image(uploaded_file.getvalue(), header_height, footer_height, text_input, match_case)
            if preview_img:
                st.image(preview_img, width=450)
            else:
                st.info("Preview unavailable.")

# --- FOOTER ---
st.markdown("""
<div style="text-align: center; margin-top: 60px; border-top: 1px solid #E5E7EB; padding-top: 20px;">
    <img src="https://visitor-badge.laobi.icu/badge?page_id=pdfwatermarkremover.streamlit.app&left_text=Total%20Visits&left_color=%231F2937&right_color=%232563EB" alt="Visitor Count">
</div>
""", unsafe_allow_html=True)
