# app.py
import streamlit as st
from parser import parse_resume
from utils import save_json, parsed_to_dataframe
import pandas as pd
from pathlib import Path
import tempfile

st.set_page_config(page_title="Smart Resume Parser", layout="wide")

st.title("Smart Resume Parser")
st.write("Upload PDF / DOCX / TXT resumes and extract structured data (skills, education, experience).")

uploaded = st.file_uploader("Upload one or more resumes", type=["pdf", "docx", "txt"], accept_multiple_files=True)
save_folder = Path("outputs")
save_folder.mkdir(exist_ok=True)

if st.button("Use sample resumes"):
    # show sample files list (user can pick from sample_resumes folder)
    st.info("Save the sample resume text files from the repository into `sample_resumes/` and upload them, or open them externally.")

if uploaded:
    all_parsed = []
    for file in uploaded:
        # store uploaded file temporarily then parse
        with tempfile.NamedTemporaryFile(delete=False, suffix="." + file.name.split(".")[-1]) as tmp:
            tmp.write(file.getbuffer())
            tmp_path = tmp.name
        parsed = parse_resume(tmp_path)
        all_parsed.append(parsed)

    # Show parsed results one by one with download options
    for i, parsed in enumerate(all_parsed, 1):
        st.header(f"Resume {i}: {Path(parsed['source_path']).name}")
        col1, col2 = st.columns([1, 2])
        with col1:
            st.subheader("Key fields")
            st.write("**Name:**", parsed.get("name"))
            st.write("**Email:**", parsed.get("email"))
            st.write("**Phone:**", parsed.get("phone"))
            st.write("**Skills:**", ", ".join(parsed.get("skills", [])) or "—")
            st.write("**# Education items:**", len(parsed.get("education", [])))
            st.write("**# Experience items:**", len(parsed.get("experience", [])))
        with col2:
            st.subheader("Preview JSON")
            st.json(parsed)

        # allow export
        json_path = save_folder / f"parsed_resume_{i}.json"
        save_json(parsed, json_path)
        df = parsed_to_dataframe(parsed)
        csv_path = save_folder / f"parsed_resume_{i}.csv"
        df.to_csv(csv_path, index=False)
        st.download_button("Download JSON", data=open(json_path, "rb"), file_name=json_path.name)
        st.download_button("Download CSV", data=open(csv_path, "rb"), file_name=csv_path.name)

    # aggregate to a combined CSV
    combined_df = pd.concat([parsed_to_dataframe(p) for p in all_parsed], ignore_index=True)
    combined_path = save_folder / "combined_parsed.csv"
    combined_df.to_csv(combined_path, index=False)
    st.success(f"Saved {len(all_parsed)} parsed results to {save_folder}/")
    st.download_button("Download combined CSV", data=open(combined_path, "rb"), file_name=combined_path.name)
else:
    st.info("Upload resumes to get started. There are sample resume texts in the repository you can save and upload.")
