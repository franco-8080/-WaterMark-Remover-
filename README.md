#  Watermark Remover-PDF 💧

**PDF Watermark Remover** is a secure, automated utility designed to clean unwanted artifacts—such as text watermarks, logos, headers, and footers—from PDF documents.

Unlike many online tools that require you to upload your sensitive files to a remote server, **PDF Watermark Remover** processes everything locally in your browser's memory using Python. Your documents never leave your computer.

---

## 🚀 Key Features

* **⚡ Auto-Detection Engine:** Automatically scans your document to identify repetitive text patterns (common in watermarks) and suggests keywords to remove.
* **🎨 Smart Inpainting:** When text is removed, the engine dynamically samples the surrounding background color to "heal" the gap, making the edit invisible.
* **✂️ Precision Edge Trimming:** Easily white-out top headers or bottom footers to remove page numbers, tracking codes, or stubborn logos.
* **👁️ Real-Time Preview:** See exactly what your cleaned PDF will look like before you download it.
* **🛡️ 100% Private & Secure:** Built on Streamlit and PyMuPDF, ensuring all processing happens locally on your machine.

---

## 🛠️ Installation

### Prerequisites
* Python 3.8 or higher

### 1. Clone the Repository

    git clone [https://github.com/your-username/pdf-watermark-remover.git](https://github.com/your-username/pdf-watermark-remover.git)
    cd pdf-watermark-remover

### 2. Install Dependencies
This tool requires **Streamlit** for the UI, **PyMuPDF (fitz)** for PDF processing, and **Pillow** for image previews.

    pip install -r requirements.txt

*(Ensure your requirements.txt contains: streamlit, pymupdf, and Pillow)*

---

## 🖥️ Usage

Run the application using Streamlit:

    streamlit run app.py

The app will open in your default web browser (usually at http://localhost:8501).

1.  **Upload:** Drag and drop your PDF file into the upload zone.
2.  **Auto-Detect:** The app will instantly scan for watermarks and suggest keywords.
3.  **Refine:**
    * Use the **"Keywords"** box to add or remove specific text.
    * Use the **"Edge Trimmers"** sliders to cut off headers or footers.
4.  **Download:** Once the preview looks clean, click **"Download Clean PDF"**.

---

## 🔧 How It Works

1.  **Text Analysis:** The app scans the first few pages of the document. If it finds the exact same text string appearing at the same coordinates on multiple pages, it flags it as a "Watermark Candidate."
2.  **Redaction:** Using PyMuPDF, it locates the vector coordinates of the target text and removes it.
3.  **Masking:** For headers and footers, it draws a vector rectangle over the specified area, filled with the exact background color of that specific page (handling both light and dark mode documents).

---

## 🏗️ Tech Stack

* **[Streamlit](https://streamlit.io/):** For the interactive web interface.
* **[PyMuPDF (Fitz)](https://pymupdf.readthedocs.io/):** For high-performance PDF analysis and manipulation.
* **[Pillow (PIL)](https://python-pillow.org/):** For rendering page previews.

---

## 📄 License

This project is open-source and available under the MIT License.

