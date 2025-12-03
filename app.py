import streamlit as st
import fitz  # PyMuPDF
import io
import time
from PIL import Image

# --- 1. PAGE CONFIGURATION ---
st.set_page_config(
    page_title="DocPolish",
    page_icon="✨",
    layout="wide" # Wide layout needed for side-by-side preview
)

# --- 2. PREMIUM CSS ---
st.markdown("""
    <style>
    /* FORCE LIGHT THEME */
    [data-testid="stAppViewContainer"] { background-color: #FFFFFF !important; }
    [data-testid="stHeader"] { background-color: #FFFFFF !important; }
    
    /* GLOBAL FONTS */
    * { font-family: 'Inter', sans-serif !important; color: #111111; }

    /* TITLE */
    h1 {
        font-weight: 800 !important;
        letter-spacing: -0.03em !important;
        background: -webkit-linear-gradient(45deg, #820AD1, #B220E8);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 3rem !important;
        margin-bottom: 0px !important;
        padding-top: 10px !important;
    }
    
    p.subtitle {
        color: #6B7280 !important;
        font-size: 1.1rem;
        margin-top: 5px;
        margin-bottom: 30px;
        font-weight: 400;
    }

    /* UPLOAD CARD */
    [data-testid="stFileUploader"] {
        background-color: #FAFAFA; 
        border: 2px dashed #E5E7EB;
        border-radius: 20px;
        padding: 20px;
        text-align: center;
    }
    [data-testid="stFileUploader"]:hover {
        border-color: #820AD1;
        background-color: #F8F5FF;
    }

    /* PREVIEW CARD */
    .preview-box {
        border: 1px solid #E5E7EB;
        border-radius: 12px;
        padding: 10px;
        background-color: #F9FAFB;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
        text-align: center;
    }
    .preview-label {
        font-size: 0.85rem;
        color: #6B7280;
        font-weight: 600;
        margin-bottom: 10px;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }

    /* DOWNLOAD BUTTON */
    .stDownloadButton > button {
        background: linear-gradient(90deg, #820AD1 0%, #6D08AF 100%);
        color: white !important;
        border-radius: 12px !important;
        padding: 0.8rem 2rem !important;
        font-weight: 700 !important;
        font-size: 1rem !important;
        border: none !important;
        box-shadow: 0 10px 25px rgba(130, 10, 209, 0.25) !important;
        width: 100%;
        transition: transform 0.2s;
    }
    .stDownloadButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 15px 35px rgba(130, 10, 209, 0.35) !important;
    }

    /* INPUTS & SLIDER */
    .stTextInput input { border-radius: 10px; border: 1px solid #E5E7EB; }
    .stTextInput input:focus { border-color: #820AD1; box-shadow: 0 0 0 2px rgba(130,10,209,0.1); }
    div[data-baseweb="slider"] div { background-color: #820AD1 !important; }

    /* HIDE CHROME */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

# --- 3. LOGIC ---

def clean_page(page, footer_height, text_to_remove, match_case, whole_word):
    """Applies cleaning logic to a single page object"""
    # 1. MAGIC ERASER
    if text_to_remove:
        words = page.get_text("words")
        for w in words:
            word_text = w[4]
            word_rect = fitz.Rect(w[0], w[1], w[2], w[3])
            
            if match_case:
                is_match = (text_to_remove == word_text) if whole_word else (text_to_remove in word_text)
            else:
                is_match = (text_to_remove.lower() == word_text.lower()) if whole_word else (text_to_remove.lower() in word_text.lower())

            if is_match:
                page.add_redact_annot(word_rect, fill=None)
        page.apply_redactions()

    # 2. FOOTER WIPER
    if footer_height > 0:
        rect = page.rect
        # Smart color detection
        clip_rect = fitz.Rect(0, rect.height - 10, 1, rect.height - 9)
        pix = page.get_pixmap(clip=clip_rect)
        r, g, b = pix.pixel(0, 0)
        dynamic_color = (r/255, g/255, b/255)
        
        footer_rect = fitz.Rect(0, rect.height - footer_height, rect.width, rect.height)
        shape = page.new_shape()
        shape.draw_rect(footer_rect)
        shape.finish(color=dynamic_color, fill=dynamic_color, width=0)
        shape.commit()
    return page

def generate_preview(input_bytes, footer_height, text_to_remove, match_case, whole_word):
    """Generates an image of the first page with cleaning applied"""
    doc = fitz.open(stream=input_bytes, filetype="pdf")
    page = doc[0] # Get first page
    
    # Apply cleaning to this page only
    clean_page(page, footer_height, text_to_remove, match_case, whole_word)
    
    # Render to image
    pix = page.get_pixmap(dpi=150) # Moderate DPI for fast preview
    img_data = pix.tobytes("png")
    return Image.open(io.BytesIO(img_data))

def process_all_pages(input_bytes, footer_height, text_to_remove, match_case, whole_word):
    """Processes the full document"""
    doc = fitz.open(stream=input_bytes, filetype="pdf")
    output_buffer = io.BytesIO()
    doc.set_metadata({}) 
    
    for page in doc:
        clean_page(page, footer_height, text_to_remove, match_case, whole_word)
    
    doc.save(output_buffer)
    output_buffer.seek(0)
    return output_buffer, len(doc)

# --- 4. THE UI ---

c_main_1, c_main_2 = st.columns([1, 1], gap="large")

with c_main_1:
    st.markdown('<h1>DocPolish</h1>', unsafe_allow_html=True)
    st.markdown('<p class="subtitle">Intelligent Document Cleanser</p>', unsafe_allow_html=True)
    
    uploaded_file = st.file_uploader("Upload PDF Document", type="pdf")
    
    if uploaded_file:
        st.write("---")
        
        # CONTROLS
        st.markdown("### 🪄 Magic Eraser")
        col_in, col_tog = st.columns([2, 1])
        with col_in:
            text_to_remove = st.text_input("Text to remove", placeholder="e.g. Confidential", label_visibility="collapsed")
        with col_tog:
            match_case = st.checkbox("Match Case", value=False)
            whole_word = st.checkbox("Whole Word", value=True)
            
        st.write("")
        st.markdown("### 📐 Footer Wiper")
        # SLIDER 0-100 as requested
        footer_height = st.slider("Cleaning Height (pixels)", 0, 100, 0)
        st.caption("Adjust slider to cover bottom text. Look at the preview!")

with c_main_2:
    if uploaded_file:
        st.write("")
        st.write("")
        st.markdown('<div class="preview-label">LIVE PREVIEW (PAGE 1)</div>', unsafe_allow_html=True)
        
        # PREVIEW CONTAINER
        with st.container():
            # Show a spinner while the preview generates (happens fast)
            with st.spinner("Updating preview..."):
                preview_img = generate_preview(
                    uploaded_file.getvalue(), 
                    footer_height, 
                    text_to_remove, 
                    match_case, 
                    whole_word
                )
                
                # Display Image with a nice border
                st.image(preview_img, use_container_width=True)
                st.caption("This is how your document will look.")

# --- 5. DOWNLOAD SECTION (Full Width Bottom) ---
if uploaded_file:
    st.write("---")
    
    # We only show the download button if changes are made or user is ready
    c_down_1, c_down_2, c_down_3 = st.columns([1, 2, 1])
    
    with c_down_2:
        if st.button("✨ Process & Download Full Document", type="primary"):
            with st.spinner("Processing entire document... Please wait."):
                # Process Full Doc
                cleaned_data, page_count = process
