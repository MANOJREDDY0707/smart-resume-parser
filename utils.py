# utils.py
import json
import pandas as pd
from pathlib import Path

def save_json(obj, path):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2)

def parsed_to_dataframe(parsed):
    # Flatten to a single-row DataFrame for quick preview and CSV export
    flattened = {
        "name": parsed.get("name"),
        "email": parsed.get("email"),
        "phone": parsed.get("phone"),
        "skills": ";".join(parsed.get("skills", [])),
        "organizations": ";".join(parsed.get("organizations", [])),
        "dates": ";".join(parsed.get("dates_mentioned", []))
    }
    # flatten education/experience counts
    flattened["education_count"] = len(parsed.get("education", []))
    flattened["experience_count"] = len(parsed.get("experience", []))
    return pd.DataFrame([flattened])
