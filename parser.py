# parser.py
import re
import fitz  # PyMuPDF
import docx
import json
from collections import defaultdict
import spacy
import os

EMAIL_RE = re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+")
PHONE_RE = re.compile(r"(?:\+?\d{1,3}[\s-]?)?(?:\(?\d{2,4}\)?[\s-]?)?[\d\s-]{7,15}")
DATE_RE = re.compile(r"\b(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|"
                     r"Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?|"
                     r"\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\d{4})\b", re.I)

SECTION_HEADERS = [
    r"summary", r"objective", r"skills", r"technical skills", r"education", r"experience",
    r"work experience", r"professional experience", r"projects", r"certifications",
    r"awards", r"publications", r"languages", r"interests"
]

# safe spaCy load with fallback to blank English if model not available
try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    # fallback: no NER available but pipeline still usable for tokenization
    nlp = spacy.blank("en")

# improve section heading regex to capture heading and optional inline content after colon
SECTION_START_RE = re.compile(r"^\s*(%s)\s*[:\-]?\s*(.*)$" % "|".join(SECTION_HEADERS), re.I)

COMMON_SKILLS = [
    # add more as needed
    "python", "java", "c++", "c#", "javascript", "react", "node", "sql",
    "postgres", "mongodb", "aws", "azure", "docker", "kubernetes",
    "linux", "git", "html", "css", "tensorflow", "pytorch", "nlp", "spaCy", "pandas"
]

def extract_text_from_pdf(path):
    text_chunks = []
    doc = fitz.open(path)
    for page in doc:
        text = page.get_text("text")
        if text:
            text_chunks.append(text)
    return "\n".join(text_chunks)

def extract_text_from_docx(path):
    doc = docx.Document(path)
    paragraphs = [p.text for p in doc.paragraphs if p.text and p.text.strip()]
    return "\n".join(paragraphs)

def load_text(path):
    path = str(path)
    if path.lower().endswith(".pdf"):
        return extract_text_from_pdf(path)
    if path.lower().endswith(".docx"):
        return extract_text_from_docx(path)
    # allow txt fallback
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        return f.read()

def preprocess_text(text):
    # Normalize line endings and remove excessive spaces
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    # replace multiple blank lines with two
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()

def split_sections(text):
    """
    Split text by common section headings. Returns list of (heading, content).
    If a heading has inline content (e.g. "Skills: Python, Java") the inline content is
    treated as the first line of that section.
    """
    lines = text.splitlines()
    sections = []
    current_heading = "header"
    buffer = []
    for line in lines:
        m = SECTION_START_RE.match(line)
        if m:
            # flush
            if buffer:
                sections.append((current_heading.lower(), "\n".join(buffer).strip()))
            current_heading = m.group(1).strip()
            buffer = []
            inline = m.group(2).strip() if m.group(2) else ""
            if inline:
                buffer.append(inline)
        else:
            buffer.append(line)
    if buffer:
        sections.append((current_heading.lower(), "\n".join(buffer).strip()))
    return sections

def find_email(text):
    m = EMAIL_RE.search(text)
    return m.group(0) if m else None

def find_phone(text):
    # return first reasonably sized phone match after filtering tiny numbers
    for m in PHONE_RE.finditer(text):
        s = m.group(0)
        # preserve leading '+' if present, otherwise keep digits only
        plus = "+" if s.strip().startswith("+") else ""
        digits = re.sub(r"[^\d]", "", s)
        if 7 <= len(digits) <= 15:
            return plus + digits
    return None

def extract_skills_section(sections):
    # Prefer section headings containing "skill"
    skills = set()
    all_content = " ".join(s[1] for s in sections)
    for heading, content in sections:
        if "skill" in heading.lower() or "technical" in heading.lower():
            tokens = re.split(r"[,\n;•\u2022]", content)
            for tok in tokens:
                tok = tok.strip()
                if tok:
                    skills.add(tok.lower())
    # fallback: keyword scan in whole text
    if not skills:
        for kw in COMMON_SKILLS:
            if re.search(r"\b" + re.escape(kw) + r"\b", all_content, re.I):
                skills.add(kw.lower())
    # normalize some common variants (e.g., spaCy -> spacy)
    normalized = {s.strip() for s in skills if s}
    return sorted(normalized)

def extract_education(sections):
    edus = []
    for heading, content in sections:
        if "education" in heading.lower():
            # split by lines and try to parse degree, institution, year
            for line in content.splitlines():
                line = line.strip()
                if not line: 
                    continue
                year = None
                y = re.search(r"\b(19|20)\d{2}\b", line)
                if y:
                    year = y.group(0)
                edus.append({"text": line, "year": year})
    return edus

def extract_experience(sections):
    experiences = []
    for heading, content in sections:
        if "experience" in heading.lower() or "professional" in heading.lower() or "work" in heading.lower():
            # naive splitting: blank line separated entries or lines that look like 'Title — Company (Dates)'
            chunks = re.split(r"\n{2,}", content)
            if len(chunks) == 1:
                chunks = content.splitlines()
            for c in chunks:
                t = c.strip()
                if not t:
                    continue
                # find dates
                dates = DATE_RE.findall(t)
                experiences.append({"text": t, "dates": list(set(dates))})
    # fallback: use NER to look for ORG + DATE spans in whole doc
    if not experiences:
        doc = nlp(" ".join(s[1] for s in sections))
        # group sentences containing ORG and DATE
        for sent in doc.sents:
            ents = {e.label_ for e in sent.ents}
            if "ORG" in ents:
                ex = {"text": sent.text.strip(),
                      "dates": [e.text for e in sent.ents if e.label_ in ("DATE", "TIME")]}
                experiences.append(ex)
    return experiences

def extract_name(text):
    # heuristic: use spaCy NER: first PERSON entity near top of doc
    doc = nlp(text[:1000])
    for ent in doc.ents:
        if ent.label_ == "PERSON":
            return ent.text
    # fallback: first line
    first_line = text.strip().splitlines()[0]
    if len(first_line.split()) <= 4 and any(c.isalpha() for c in first_line):
        return first_line.strip()
    return None

def parse_resume(path):
    raw_text = load_text(path)
    text = preprocess_text(raw_text)
    sections = split_sections(text)
    data = {}
    data["source_path"] = str(path)
    data["name"] = extract_name(text)
    data["email"] = find_email(text)
    data["phone"] = find_phone(text)
    data["skills"] = extract_skills_section(sections)
    data["education"] = extract_education(sections)
    data["experience"] = extract_experience(sections)
    # use spaCy to get additional fields: orgs, locations
    doc = nlp(text)
    orgs = sorted({ent.text for ent in doc.ents if ent.label_ == "ORG"})
    dates = sorted({ent.text for ent in doc.ents if ent.label_ == "DATE"})
    data["organizations"] = orgs
    data["dates_mentioned"] = dates
    data["raw_text_snippet"] = text[:2000]  # keep first 2k chars
    return data

if __name__ == "__main__":
    import sys, pprint
    p = sys.argv[1]
    out = parse_resume(p)
    pprint.pprint(out)
    # write json next to input - ensure directory exists
    out_dir = os.path.join("outputs")
    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, "sample_parsed.json"), "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2)
