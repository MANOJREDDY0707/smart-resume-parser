# 🧠 Smart Resume Parser

A Streamlit-based web app that automatically extracts structured information — such as **Skills, Education, and Experience** — from resumes in PDF or DOCX format.

---

## 🚀 Features

- Upload PDF or DOCX resumes  
- Auto-extract key details using **spaCy NLP + regex rules**  
- View parsed results in clean, tabular format  
- Export extracted data to **JSON** or **CSV**  
- Simple **Streamlit UI** for testing and visualization  
- Includes 5 sample resumes (TXT, DOCX, and combined PDF)

---

## 🛠️ Tech Stack

| Category | Tools Used |
|-----------|-------------|
| Programming Language | Python 3.x |
| NLP Library | spaCy |
| File Parsing | PyMuPDF (for PDF), python-docx (for DOCX) |
| UI Framework | Streamlit |
| Data Handling | pandas, regex |
| Output Formats | JSON, CSV |

---

## 📂 Project Structure

smart-resume-parser/
├── app.py # Streamlit web app
├── parser.py # NLP and extraction logic
├── utils.py # Helper functions
├── make_resumes.py # Script to generate sample resumes
├── requirements.txt # Python dependencies
├── sample_resumes/ # 5 sample resumes (txt, docx, pdf)
│ ├── resume1.txt
│ ├── resume1.docx
│ ├── ...
│ └── all_resumes.pdf
├── outputs/ # Stores generated CSV/JSON files
└── README.md # Documentation

---

## ⚙️ Installation & Setup

1. **Clone or unzip** the project folder:
   ```bash
   cd smart-resume-parser
python -m venv venv
venv\Scripts\activate   # On Windows

pip install -r requirements.txt
python -m spacy download en_core_web_sm
streamlit run app.py
streamlit run app.py
