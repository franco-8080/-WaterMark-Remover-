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

# --- 2. ADVANCED CSS STYLING ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }

    /* PROTECT ICONS */
    [data-testid="stExpander"] svg, [class*="material-symbols"], .st-emotion-cache-1pbqwg9 {
        font-family: 'Material Symbols Rounded' !important;
    }

    /* Uploader Styling */
    [data-testid="stFileUploader"] {
        background-color: #FFFFFF;
        border: 2px dashed #E5E7EB;
        border-radius: 20px;
        padding: 30px;
        transition: all 0.3s ease;
    }
    [data-testid="stFileUploader"]:hover {
        border-color: #3B82F6;
        background-color: #EFF6FF;
    }

    /* Notification Box */
    .auto-detect-box {
        background: linear-gradient(to right, #EFF6FF, #DBEAFE);
        border: 1px solid #BFDBFE;
        color: #1E40AF;
        padding: 12px 20px;
        border-radius: 12px;
        font-size: 0.95rem;
        margin-bottom: 20px;
    }

    /* Headers */
    .hero-container {
        text-align: center;
        margin-bottom: 40px;
        padding: 20px 0;
    }
    .hero-title {
        font-weight: 800;
        background: linear-gradient(135deg, #2563EB 0%, #06B6D4 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 3.5rem;
        letter-spacing: -1px;
        margin-bottom: 8px;
    }
    .hero-subtitle {
        color: #6B7280;
        font-size: 1.2rem;
        font-weight: 400;
    }

    /* Button Styling */
    .stDownloadButton > button {
        background: linear-gradient(135deg, #2563EB 0%, #06B6D4 100%);
        color: white !important;
        border: none;
        padding: 0.6rem 2rem;
        border-radius: 10px;
        font-weight: 600;
        width: 100%;
        transition: all 0.3s ease;
    }
    .stDownloadButton > button:hover {
        box-shadow: 0 10px 15px -3px rgba(37, 99, 235, 0.4);
        transform: translateY(-2px);
    }
    
    [data-testid="stHeader"], footer { display: none !important; }
    .block-container { padding-top: 2rem !important; }
    div[data-testid="stImage"] { display: flex; justify-content: center; }
    </style>
""", unsafe_allow_html=True)

# --- 3. LOGIC ---

def detect_watermark_candidates(file_bytes):
    """
    Improved detection logic:
    1. Scans line-by-line (split by \\n) to catch watermarks that share a text block.
    2. Specifically checks for 'NotebookLM' as per user request.
    """
    doc = fitz.open(stream=file_bytes, filetype="pdf")
    # Scan up to 10 pages for better accuracy
    page_limit = min(10, len(doc)) 
    line_counts = Counter()
    
    for i in range(page_limit):
        page = doc[i]
        # Get text as a simple string and split by lines
        text_content = page.get_text("text")
        lines = [line.strip() for line in text_content.split('\n') if len(line.strip()) > 2]
        line_counts.update(lines)

    # Threshold: Text must appear on at least 40% of scanned pages to be a "watermark"
    threshold = max(2, int(page_limit * 0.4))
    suggestions = [text for text, count in line_counts.items() if count >= threshold]
    
    # Specific rule for your requested watermark
    if "NotebookLM" in line_counts and "NotebookLM" not in suggestions:
        suggestions.append("NotebookLM")

    return ", ".join(suggestions)

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
                # Remove the text
                page.add_redact_annot(quad, fill=None)
        page.apply_redactions()

    rect = page.rect
    # 2. Smart color detection (samples near bottom edge)
    clip = fitz.Rect(0, rect.height-10, 1, rect.height-9)
    pix = page.get_pixmap(clip=clip)
    r, g, b = pix.pixel(0, 0)
    dynamic_color = (r/255, g/255, b/255)

    # 3. Area Wiping (Header/Footer)
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
    # Remove metadata which might also contain watermark info
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

# UPLOAD
c1, c2, c3 = st.columns([1, 6, 1])
with c2:
    uploaded_file = st.file_uploader("Drop your PDF here to start", type="pdf", label_visibility="collapsed")

# STATE MANAGEMENT
if uploaded_file:
    file_bytes = uploaded_file.getvalue()
    
    # Initialize State if new file
    if "current_file" not in st.session_state or st.session_state.current_file != uploaded_file.name:
        st.session_state.current_file = uploaded_file.name
        with st.spinner("🔍 Scanning for watermarks..."):
            st.session_state.auto_keywords = detect_watermark_candidates(file_bytes)
            st.session_state.header_val = 0
            st.session_state.footer_val = 0
            st.session_state.text_val = st.session_state.auto_keywords

if not uploaded_file:
    st.write("")
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
        st.caption("Files are processed in secure temporary memory and are not saved to disk.")

else:
    # Check if we should keep expander open
    header_active = st.session_state.get("header_val", 0) > 0
    footer_active = st.session_state.get("footer_val", 0) > 0
    # Keep open if there are auto-detected keywords (like NotebookLM)
    text_active = len(st.session_state.get("text_val", "")) > 0 
    should_expand = header_active or footer_active or text_active

    if st.session_state.get("auto_keywords"):
        st.markdown(f"""
        <div class="auto-detect-box">
            🎯 <b>Auto-Detection:</b> Found potential watermarks: <u>{st.session_state.auto_keywords}</u>
        </div>
        """, unsafe_allow_html=True)

    with st.container(border=True):
        col_settings, col_preview = st.columns([3, 2], gap="large")
        
        with col_settings:
            st.subheader("🛠️ Removal Settings")
            
            with st.expander("Advanced Options", expanded=should_expand):
                
                st.markdown("**📝 Text Watermarks**")
                text_input = st.text_input(
                    "Keywords", 
                    key="text_val",
                    help="Enter specific words to erase (e.g., 'NotebookLM'). Separate multiple words with commas."
                )
                match_case = st.checkbox(
                    "Match Case", 
                    value=False,
                    help="If checked, only exact case matches will be removed."
                )
                
                st.markdown("---")
                
                st.markdown("**✂️ Header & Footer Cutters**")
                header_height = st.slider(
                    "Top Margin Cut", 0, 150, 
                    key="header_val",
                    help="White-outs the top X pixels of every page."
                )
                footer_height = st.slider(
                    "Bottom Margin Cut", 0, 150, 
                    key="footer_val",
                    help="White-outs the bottom X pixels of every page."
                )

            st.write("")
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
