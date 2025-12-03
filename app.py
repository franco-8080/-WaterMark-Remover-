import streamlit as st
import fitz  # PyMuPDF
import io
import time

# --- 1. PAGE CONFIGURATION ---
st.set_page_config(
    page_title="DocPolish",
    page_icon="✨",
    layout="centered"
)

# --- 2. BEAUTIFUL & CLEAN CSS ---
st.markdown("""
    <style>
    /* FORCE LIGHT THEME */
    [data-testid="stAppViewContainer"] { background-color: #FFFFFF !important; }
    [data-testid="stHeader"] { background-color: #FFFFFF !important; }
    
    /* GLOBAL FONTS */
    * { font-family: 'Inter', sans-serif !important; color: #111111; }

    /* TITLE - Gradient Purple */
    h1 {
        font-weight: 800 !important;
        letter-spacing: -0.03em !important;
        background: -webkit-linear-gradient(45deg, #820AD1, #B220E8);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 3.5rem !important;
        text-align: center;
        margin-bottom: 0px !important;
        padding-top: 10px !important;
    }
    
    p.subtitle {
        text-align: center;
        color: #6B7280 !important;
        font-size: 1.1rem;
        margin-top: 5px;
        margin-bottom: 40px;
        font-weight: 400;
    }

    /* UPLOAD CARD - Glassmorphism Feel */
    [data-testid="stFileUploader"] {
        background-color: #FAFAFA; 
        border: 2px dashed #E5E7EB;
        border-radius: 20px;
        padding: 40px;
        text-align: center;
        transition: all 0.2s;
    }
    [data-testid="stFileUploader"]:hover {
        border-color: #820AD1;
        background-color: #F8F5FF;
    }

    /* TOOL CARDS (Containers) */
    .tool-card {
        background-color: #FFFFFF;
        border: 1px solid #F3F4F6;
        border-radius: 16px;
        padding: 20px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
        margin-bottom: 15px;
    }
    
    /* SUCCESS NOTIFICATION */
    .success-toast {
        background-color: #ECFDF5;
        color: #047857;
        padding: 16px;
        border-radius: 12px;
        font-weight: 600;
        text-align: center;
        border: 1px solid #D1FAE5;
        margin-top: 20px;
        margin-bottom: 20px;
        box-shadow: 0 4px 12px rgba(16, 185, 129, 0.1);
    }

    /* DOWNLOAD BUTTON - Large & Prominent */
    .stDownloadButton > button {
        background: linear-gradient(90deg, #820AD1 0%, #6D08AF 100%);
        color: white !important;
        border-radius: 12px !important;
        padding: 1rem 2rem !important;
        font-weight: 700 !important;
        font-size: 1.1rem !important;
        border: none !important;
        box-shadow: 0 10px 25px rgba(130, 10, 209, 0.25) !important;
        width: 100%;
        transition: transform 0.2s;
    }
    .stDownloadButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 15px 35px rgba(130, 10, 209, 0.35) !important;
    }

    /* INPUT FIELDS */
    .stTextInput input {
        border-radius: 10px;
        border: 1px solid #E5E7EB;
    }
    .stTextInput input:focus {
        border-color: #820AD1;
        box-shadow: 0 0 0 2px rgba(130,10,209,0.1);
    }

    /* HIDE CHROME */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

# --- 3. PROCESSING LOGIC ---
def process_pdf(input_bytes, footer_height, text_to_remove, match_case, whole_word):
    doc = fitz.open(stream=input_bytes, filetype="pdf")
    output_buffer = io.BytesIO()
    doc.set_metadata({}) # Privacy Scrub
    
    for page in doc:
        # 1. MAGIC ERASER (Text)
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

        # 2. FOOTER WIPER (Area)
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
    
    doc.save(output_buffer)
    output_buffer.seek(0)
    return output_buffer, len(doc)

# --- 4. THE UI ---

# Header
st.markdown('<h1>DocPolish</h1>', unsafe_allow_html=True)
st.markdown('<p class="subtitle">Intelligent Document Cleanser</p>', unsafe_allow_html=True)

# Main Container
c1, c2, c3 = st.columns([1, 8, 1])

with c2:
    uploaded_file = st.file_uploader("Upload PDF Document", type="pdf")
    
    if uploaded_file:
        st.write("")
        
        # --- CARD 1: MAGIC ERASER ---
        st.markdown('<div class="tool-card">', unsafe_allow_html=True)
        st.markdown("### 🪄 Magic Eraser")
        st.caption("Removes specific words (e.g. 'Confidential', 'Draft') from anywhere on the page.")
        
        col_in, col_tog = st.columns([2, 1])
        with col_in:
            text_to_remove = st.text_input("Text to remove", placeholder="Type word here...", label_visibility="collapsed")
        with col_tog:
            match_case = st.checkbox("Match Case", value=False)
            whole_word = st.checkbox("Whole Word", value=True)
        st.markdown('</div>', unsafe_allow_html=True)


        # --- CARD 2: FOOTER POLISH ---
        st.markdown('<div class="tool-card">', unsafe_allow_html=True)
        st.markdown("### 📐 Footer Wiper")
        st.caption("The 'Nuclear Option'. Use this to wipe logos, lines, or page numbers from the bottom.")
        
        # SLIDER (Native Streamlit style - fixed!)
        footer_height = st.slider("Cleaning Height (pixels)", 0, 150, 0)
        st.markdown('</div>', unsafe_allow_html=True)
        
        
        # --- ACTION ---
        if footer_height > 0 or text_to_remove:
            with st.spinner("✨ Polishing pixels..."):
                cleaned_data, page_count = process_pdf(uploaded_file.getvalue(), footer_height, text_to_remove, match_case, whole_word)
                time.sleep(0.5)
            
            # Success Toast
            st.markdown(f'<div class="success-toast">✅ Successfully Polished {page_count} Pages</div>', unsafe_allow_html=True)
            
            # Download
            st.download_button(
                label="Download Clean PDF",
                data=cleaned_data,
                file_name=f"Clean_{uploaded_file.name}",
                mime="application/pdf"
            )
