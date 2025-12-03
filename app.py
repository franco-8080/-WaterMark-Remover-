import streamlit as st
import fitz  # PyMuPDF
import io

# --- 1. CONFIGURATION ---
st.set_page_config(
    page_title="DocPolish | Watermark Remover",
    page_icon="✨",
    layout="centered"
)

# --- 2. TRUSTWORTHY STYLING (Fixed & Clean) ---
st.markdown("""
    <style>
    /* FORCE LIGHT THEME (Overrides Dark Mode) */
    [data-testid="stAppViewContainer"] {
        background-color: #F8FAFC !important; /* Very light slate grey */
    }
    [data-testid="stHeader"] {
        background-color: #F8FAFC !important;
    }
    [data-testid="stSidebar"] {
        background-color: #FFFFFF !important;
    }
    
    /* TEXT COLORS - Force Dark Grey for Readability */
    h1, h2, h3, p, div, span, label, li {
        color: #0F172A !important; /* Slate 900 (Almost Black) */
        font-family: 'Segoe UI', sans-serif;
    }
    
    /* TITLE STYLING */
    .main-title {
        text-align: center;
        font-size: 2.5rem !important;
        font-weight: 800 !important;
        color: #2563EB !important; /* Royal Blue */
        margin-bottom: 0px;
    }
    .sub-title {
        text-align: center;
        font-size: 1.1rem !important;
        color: #64748B !important; /* Muted Slate */
        margin-bottom: 2rem;
        font-weight: 400;
    }

    /* CARD STYLING (The Uploader Box) */
    [data-testid="stFileUploader"] {
        background-color: #FFFFFF;
        border: 1px dashed #CBD5E1;
        padding: 2rem;
        border-radius: 12px;
    }
    
    /* SUCCESS BOX STYLING */
    .success-box {
        padding: 1rem;
        border-radius: 8px;
        background-color: #DCFCE7; /* Light Green */
        border: 1px solid #16A34A;
        color: #166534 !important;
        text-align: center;
        margin-bottom: 1rem;
        font-weight: 600;
    }

    /* DOWNLOAD BUTTON STYLING */
    .stDownloadButton > button {
        background-color: #2563EB !important; /* Blue */
        color: white !important;
        width: 100%;
        border-radius: 8px;
        height: 3.5rem;
        font-weight: 600;
        border: none;
        box-shadow: 0 4px 6px -1px rgba(37, 99, 235, 0.2);
    }
    .stDownloadButton > button:hover {
        background-color: #1D4ED8 !important;
        box-shadow: 0 10px 15px -3px rgba(37, 99, 235, 0.3);
    }

    /* HIDE MENU */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

# --- 3. PROCESSING LOGIC ---
def process_pdf(input_bytes, footer_height):
    doc = fitz.open(stream=input_bytes, filetype="pdf")
    output_buffer = io.BytesIO()
    
    for page in doc:
        rect = page.rect
        # 1. Smart Color Detection (Bottom Left pixel)
        clip_rect = fitz.Rect(0, rect.height - 10, 1, rect.height - 9)
        pix = page.get_pixmap(clip=clip_rect)
        r, g, b = pix.pixel(0, 0)
        dynamic_color = (r/255, g/255, b/255)
        
        # 2. Draw Box over Footer
        footer_rect = fitz.Rect(0, rect.height - footer_height, rect.width, rect.height)
        shape = page.new_shape()
        shape.draw_rect(footer_rect)
        shape.finish(color=dynamic_color, fill=dynamic_color, width=0)
        shape.commit()
    
    doc.save(output_buffer)
    output_buffer.seek(0)
    return output_buffer, len(doc)

# --- 4. THE UI ---

# Header
st.markdown('<div class="main-title">DocPolish</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">Remove watermarks & footers instantly.</div>', unsafe_allow_html=True)

# Main Container
with st.container():
    # 1. Upload
    uploaded_file = st.file_uploader("Upload your PDF file", type="pdf")
    
    # 2. Settings (Clean & Simple)
    if uploaded_file:
        st.write("---")
        st.markdown("**Cleaning Depth** (Adjust if text is still visible)")
        # Standard Streamlit slider (No custom CSS to avoid the "Block" bug)
        footer_height = st.slider("", 10, 100, 30, label_visibility="collapsed")
        
        # 3. AUTO-PROCESS & DOWNLOAD
        # As requested: "Direct give option to download"
        # We process immediately so the button is ready.
        with st.spinner("Polishing your document..."):
            cleaned_data, page_count = process_pdf(uploaded_file.getvalue(), footer_height)
        
        # Success Message
        st.markdown(f'<div class="success-box">✨ Ready! {page_count} pages cleaned.</div>', unsafe_allow_html=True)
        
        # The Download Button
        st.download_button(
            label="Download Clean PDF",
            data=cleaned_data,
            file_name=f"Clean_{uploaded_file.name}",
            mime="application/pdf"
        )

# Footer Trust Signals
if not uploaded_file:
    st.write("")
    st.write("")
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown("<div style='text-align: center; color: #2563EB; font-size: 1.5rem;'>🔒</div>", unsafe_allow_html=True)
        st.markdown("<div style='text-align: center; font-size: 0.85rem;'>100% Private</div>", unsafe_allow_html=True)
    with c2:
        st.markdown("<div style='text-align: center; color: #2563EB; font-size: 1.5rem;'>⚡</div>", unsafe_allow_html=True)
        st.markdown("<div style='text-align: center; font-size: 0.85rem;'>Instant</div>", unsafe_allow_html=True)
    with c3:
        st.markdown("<div style='text-align: center; color: #2563EB; font-size: 1.5rem;'>✨</div>", unsafe_allow_html=True)
        st.markdown("<div style='text-align: center; font-size: 0.85rem;'>Watermark Free</div>", unsafe_allow_html=True)