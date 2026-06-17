import os
import re
import base64
from pypdf import PdfReader

GUIDELINES_PATH = "medical_guidelines.txt"

def retrieve_guidelines_context(text: str) -> str:
    """Searches medical_guidelines.txt sections and returns matching ground truths."""
    if not os.path.exists(GUIDELINES_PATH):
        return ""
    
    try:
        with open(GUIDELINES_PATH, "r", encoding="utf-8") as f:
            content = f.read()
    except Exception:
        return ""
        
    sections = content.split("CLINICAL REFERENCE GUIDELINE:")
    retrieved_sections = []
    
    text_lower = text.lower()
    for sec in sections:
        if not sec.strip():
            continue
        
        # Split title to map target keywords
        lines = sec.strip().split("\n")
        title = lines[0].lower() if lines else ""
        
        keywords = []
        if "hemoglobin (hba1c)" in title or "glycated hemoglobin" in title or "diabetes" in title:
            keywords = ["hba1c", "glycated", "glucose", "a1c", "diabetes", "diabetic"]
        elif "blood pressure" in title or "hypertension" in title:
            keywords = ["blood pressure", "bp", "hypertension", "systolic", "diastolic", "hypertensive"]
        elif "lipid" in title or "cholesterol" in title:
            keywords = ["lipid", "cholesterol", "ldl", "hdl", "triglycerides", "hyperlipidemia"]
        elif "hemoglobin (hb)" in title or "anemia" in title:
            keywords = ["hemoglobin", "hb", "hgb", "anemia", "anemic", "oxygen transport"]
            
        if any(re.search(r'\b' + re.escape(kw) + r'\b', text_lower) for kw in keywords):
            retrieved_sections.append(f"CLINICAL REFERENCE GUIDELINE: {sec.strip()}")
            
    return "\n\n".join(retrieved_sections)

def encode_image_base64(image_bytes: bytes) -> str:
    """Encodes raw image bytes into a base64 string."""
    return base64.b64encode(image_bytes).decode("utf-8")

def parse_pdf_text(pdf_file) -> str:
    """Reads PDF binary data and extracts readable alphanumeric character segments."""
    try:
        reader = PdfReader(pdf_file)
        text = ""
        for page in reader.pages:
            parsed = page.extract_text()
            if parsed:
                text += parsed + "\n"
        return text
    except Exception as e:
        print(f"Error parsing PDF document: {e}")
        return ""

def parse_metrics_regex(text: str) -> dict:
    """Locally parses lab parameters from query text to render Streamlit Dashboard widgets."""
    text_lower = text.lower()
    metrics = {}
    
    # 1. HbA1c
    hba1c_match = re.search(r'(?:hba1c|glycated hemoglobin|a1c)[\s:]*([0-9\.]+)', text_lower)
    if hba1c_match:
        metrics["hba1c"] = float(hba1c_match.group(1))
        
    # 2. Blood Pressure
    bp_match = re.search(r'(?:bp|blood pressure)?[\s:]*\b([0-9]{2,3})\s*/\s*([0-9]{2,3})\b', text_lower)
    if bp_match:
        metrics["bp"] = {
            "sys": int(bp_match.group(1)),
            "dia": int(bp_match.group(2))
        }
        
    # 3. LDL Cholesterol
    ldl_match = re.search(r'ldl[\s:]*([0-9\.]+)', text_lower)
    if ldl_match:
        metrics["ldl"] = float(ldl_match.group(1))
        
    # 4. Hemoglobin
    hb_match = re.search(r'(?:hemoglobin|hb|hgb)[\s:]*([0-9\.]+)', text_lower)
    if hb_match:
        metrics["hb"] = float(hb_match.group(1))
        
    return metrics
