import os
import re
import base64
import requests
from io import BytesIO
from PIL import Image
import streamlit as st

from rag_utils import (
    retrieve_guidelines_context,
    encode_image_base64,
    parse_pdf_text,
    parse_metrics_regex
)

# =====================================================================
# SYSTEM & CONFIGURATION SETUP
# =====================================================================
st.set_page_config(
    page_title="Clinical-RAG: Live Universal Medical Engine",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Premium CSS Injection for Dark Health-Tech Visual Style
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;700&display=swap');
    
    /* Global Styles */
    html, body, [data-testid="stAppViewContainer"], .stApp {
        font-family: 'Outfit', sans-serif !important;
        background-color: #080c14;
        color: #e2e8f0;
    }
    
    /* Header Card styling */
    .header-card {
        background: linear-gradient(135deg, rgba(16, 23, 42, 0.8) 0%, rgba(8, 12, 21, 0.95) 100%);
        backdrop-filter: blur(16px);
        border: 1px solid rgba(0, 229, 255, 0.2);
        border-radius: 16px;
        padding: 28px;
        margin-bottom: 28px;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.5), 0 0 20px rgba(0, 229, 255, 0.05);
        text-align: left;
    }
    
    .header-title {
        font-family: 'Outfit', sans-serif;
        font-weight: 800;
        font-size: 34px;
        color: #ffffff;
        background: linear-gradient(135deg, #ffffff 0%, #00e5ff 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 6px;
        display: flex;
        align-items: center;
        gap: 12px;
        letter-spacing: -0.02em;
    }
    
    .header-subtitle {
        font-family: 'Outfit', sans-serif;
        font-size: 15px;
        color: #94a3b8;
        font-weight: 500;
        margin: 0;
    }
    
    /* Custom Sidebar styling */
    [data-testid="stSidebar"] {
        background-color: #05080f !important;
        border-right: 1px solid rgba(0, 229, 255, 0.1) !important;
    }
    
    /* Input Areas & Select Boxes Styling */
    textarea {
        background-color: rgba(5, 8, 15, 0.7) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        color: #e2e8f0 !important;
        border-radius: 12px !important;
        font-family: 'Outfit', sans-serif !important;
        padding: 12px !important;
        transition: all 0.3s ease;
    }
    
    textarea:focus {
        border-color: #00e5ff !important;
        box-shadow: 0 0 12px rgba(0, 229, 255, 0.25) !important;
    }
    
    /* File Uploader styling */
    [data-testid="stFileUploader"] {
        background-color: rgba(5, 8, 15, 0.4) !important;
        border: 1px dashed rgba(0, 229, 255, 0.15) !important;
        border-radius: 12px !important;
        padding: 12px !important;
        transition: all 0.3s ease;
    }
    
    [data-testid="stFileUploader"]:hover {
        border-color: #00e5ff !important;
        background-color: rgba(0, 229, 255, 0.02) !important;
    }
    
    /* Buttons with glowing premium health-tech style */
    div.stButton > button {
        background: linear-gradient(135deg, #00e5ff 0%, #0b84fe 100%) !important;
        color: #ffffff !important;
        border: none !important;
        padding: 12px 24px !important;
        border-radius: 10px !important;
        font-family: 'Outfit', sans-serif !important;
        font-weight: 700 !important;
        font-size: 16px !important;
        letter-spacing: 0.02em;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
        box-shadow: 0 4px 14px rgba(0, 229, 255, 0.3) !important;
        width: 100%;
        margin-top: 10px;
    }
    
    div.stButton > button:hover {
        background: linear-gradient(135deg, #00f0ff 0%, #00aaff 100%) !important;
        box-shadow: 0 6px 20px rgba(0, 229, 255, 0.5) !important;
        transform: translateY(-2px);
    }
    
    div.stButton > button:active {
        transform: translateY(1px);
    }
    
    /* Metric Card styling */
    .metric-card-custom {
        background: linear-gradient(135deg, rgba(255, 255, 255, 0.01) 0%, rgba(255, 255, 255, 0.03) 100%);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 14px;
        padding: 18px;
        margin-bottom: 14px;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
    }
    
    .metric-card-custom:hover {
        border-color: rgba(0, 229, 255, 0.35);
        background: linear-gradient(135deg, rgba(0, 229, 255, 0.01) 0%, rgba(0, 229, 255, 0.03) 100%);
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(0, 229, 255, 0.1);
    }
    
    .metric-title {
        font-family: 'Outfit', sans-serif;
        font-size: 13px;
        font-weight: 600;
        color: #94a3b8;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 6px;
    }
    
    .metric-value {
        font-family: 'JetBrains Mono', monospace;
        font-size: 22px;
        font-weight: 700;
        color: #00e5ff;
    }
    
    .metric-zone {
        font-family: 'Outfit', sans-serif;
        font-size: 11px;
        font-weight: 600;
        margin-top: 6px;
        letter-spacing: 0.02em;
    }
    
    .zone-normal { color: #10b981; }
    .zone-borderline { color: #f59e0b; }
    .zone-danger { color: #ef4444; }
    
    /* Medical Disclaimer Callout styling */
    .disclaimer-box {
        background: rgba(239, 68, 68, 0.08) !important;
        border: 1px solid rgba(239, 68, 68, 0.2) !important;
        border-left: 5px solid #ef4444 !important;
        padding: 18px !important;
        border-radius: 8px !important;
        margin-top: 24px !important;
        box-shadow: 0 4px 12px rgba(239, 68, 68, 0.05) !important;
    }
</style>
""", unsafe_allow_html=True)

# Path configuration
GUIDELINES_PATH = "medical_guidelines.txt"

# =====================================================================
# MEDICAL PRESETS DEFINITIONS
# =====================================================================
PRESETS = {
    "Select Preset...": "",
    "Diabetic Blood Panel": (
        "PATIENT METRIC LOG\n"
        "Patient Age/Sex: 54 Years / Female\n"
        "Primary Lab Results:\n"
        "- HbA1c: 7.2 %\n"
        "- Blood Pressure: 128 / 78 mmHg\n"
        "- LDL Cholesterol: 95 mg/dL\n"
        "- Hemoglobin: 12.8 g/dL\n\n"
        "Patient Notes: Complains of mild polydipsia (excessive thirst), frequent urination, and lethargy over the past 3 months."
    ),
    "Stage 2 Hypertension": (
        "PATIENT METRIC LOG\n"
        "Patient Age/Sex: 62 Years / Male\n"
        "Primary Lab Results:\n"
        "- Blood Pressure: 142 / 92 mmHg\n"
        "- HbA1c: 5.4 %\n"
        "- LDL Cholesterol: 115 mg/dL\n"
        "- Hemoglobin: 14.5 g/dL\n\n"
        "Patient Notes: Patient reports morning headaches, high sodium intake, and high job stress."
    ),
    "Hyperlipidemia Card": (
        "PATIENT METRIC LOG\n"
        "Patient Age/Sex: 48 Years / Male\n"
        "Primary Lab Results:\n"
        "- LDL Cholesterol: 165 mg/dL\n"
        "- HDL Cholesterol: 38 mg/dL\n"
        "- Triglycerides: 210 mg/dL\n"
        "- Blood Pressure: 135 / 85 mmHg\n\n"
        "Patient Notes: Family history of coronary artery disease. Diet is high in saturated fats, patient reports sedentary lifestyle."
    ),
    "Anemic Blood Panel": (
        "PATIENT METRIC LOG\n"
        "Patient Age/Sex: 29 Years / Female\n"
        "Primary Lab Results:\n"
        "- Hemoglobin: 10.4 g/dL\n"
        "- HbA1c: 5.1 %\n"
        "- Blood Pressure: 110 / 70 mmHg\n"
        "- LDL Cholesterol: 90 mg/dL\n\n"
        "Patient Notes: Patient reports chronic fatigue, dizziness upon rising, and brittle nails."
    )
}

# =====================================================================
# SIDEBAR CONTROLS & AUTHENTICATION
# =====================================================================
st.sidebar.markdown("### 🔑 API Access Configuration")
hf_token = st.sidebar.text_input(
    "Hugging Face Access Token (HF_TOKEN)",
    type="password",
    help="Enter your Hugging Face access token to authorize serverless inference execution."
)

if not hf_token:
    st.sidebar.warning("⚠️ HF Access Token is missing. Provide token in field to activate model.")
else:
    st.sidebar.success("✅ HF Access Token provided.")

# Sidebar Preset Injector
st.sidebar.markdown("### 📋 Sample Diagnostic Presets")
preset_name = st.sidebar.selectbox("Select standard presets to fill dashboard input:", list(PRESETS.keys()))

st.sidebar.markdown("### 🧠 Model Architecture")
st.sidebar.info(
    "**Model Node:** `Qwen/Qwen2.5-VL-7B-Instruct`\n"
    "**Routing:** Hugging Face Serverless API\n"
    "**Memory Tier:** Serverless CPU Split (OOM Prevention)\n"
    "**Decode Params:** T=0.1 | Max=600 tokens"
)

# =====================================================================
# MAIN USER INTERFACE
# =====================================================================
# Glowing Header Card
st.markdown("""
<div class="header-card">
    <div class="header-title">⚡ Clinical-RAG: Universal Multimodal Analyzer</div>
    <div class="header-subtitle">Serverless Visual Diagnosis & Structured Medical RAG Pipeline utilizing Qwen2.5-VL-7B-Instruct</div>
</div>
""", unsafe_allow_html=True)

# Grid Layout: Left Column (Inputs) & Right Column (Outputs & Visualizations)
col_left, col_right = st.columns([1, 1], gap="large")

# Pre-populate preset if selected
initial_text = PRESETS.get(preset_name, "")

with col_left:
    st.markdown("### 📤 Patient Artifact Ingestion")
    
    # Text Input Area
    input_text = st.text_area(
        "Diagnostic Findings / Laboratory Results Text Box",
        value=initial_text,
        placeholder="Type patient lab metrics or paste clinical records here... (e.g. HbA1c: 7.2%, BP: 142/92 mmHg)",
        height=200
    )
    
    # File Uploader
    uploaded_file = st.file_uploader(
        "Upload Diagnostic Document or Image Scans",
        type=["txt", "pdf", "png", "jpg", "jpeg"],
        help="Upload text logs, PDF reports, or image scans (X-Rays, MRIs, Ultrasounds)."
    )
    
    # Display Preview of Uploaded Image
    file_bytes = None
    image_base64 = None
    mime_type = None
    file_text = ""
    
    if uploaded_file:
        file_bytes = uploaded_file.read()
        name_lower = uploaded_file.name.lower()
        
        if name_lower.endswith((".png", ".jpg", ".jpeg")):
            mime_type = f"image/{'png' if name_lower.endswith('png') else 'jpeg'}"
            image_base64 = encode_image_base64(file_bytes)
            
            # Display image in UI column
            st.image(Image.open(BytesIO(file_bytes)), caption="Ingested Medical Scan Image", use_column_width=True)
            
        elif name_lower.endswith(".pdf"):
            st.info(f"📄 Lab Report PDF Ingested: {uploaded_file.name}")
            # Extract PDF alphanumeric records
            file_text = parse_pdf_text(BytesIO(file_bytes))
            if file_text:
                with st.expander("Show Extracted PDF Text"):
                    st.text(file_text)
            else:
                st.warning("Could not extract raw text from PDF. Ensure PDF contains selectable text.")
                
        elif name_lower.endswith(".txt"):
            st.info(f"📝 Raw Document Ingested: {uploaded_file.name}")
            file_text = file_bytes.decode("utf-8", errors="ignore")
            with st.expander("Show Document Text"):
                st.text(file_text)

    # Trigger Buttons
    execute_analysis = st.button("🚀 Execute RAG Analysis", use_container_width=True)

# Parse inputs for RAG processing
combined_text_for_rag = input_text + "\n" + file_text

with col_right:
    st.markdown("### 📊 Interactive Lab Visualizer")
    
    # Metric extraction dashboard indicators
    metrics = parse_metrics_regex(combined_text_for_rag)
    
    if metrics:
        v_col1, v_col2 = st.columns(2)
        
        # Draw HbA1c
        if "hba1c" in metrics:
            val = metrics["hba1c"]
            zone, zone_cls = ("Normal", "zone-normal") if val < 5.7 else (("Prediabetes", "zone-borderline") if val <= 6.4 else ("Diabetes", "zone-danger"))
            with v_col1:
                st.markdown(f"""
                <div class="metric-card-custom">
                    <div class="metric-title">HbA1c Glucose</div>
                    <div class="metric-value">{val}%</div>
                    <div class="metric-zone {zone_cls}">✦ {zone} Range</div>
                </div>
                """, unsafe_allow_html=True)
                
        # Draw BP
        if "bp" in metrics:
            sys, dia = metrics["bp"]["sys"], metrics["bp"]["dia"]
            zone, zone_cls = ("Normal", "zone-normal") if (sys < 120 and dia < 80) else (("Elevated", "zone-borderline") if (sys <= 129 and dia < 80) else ("Hypertension", "zone-danger"))
            with v_col2:
                st.markdown(f"""
                <div class="metric-card-custom">
                    <div class="metric-title">Blood Pressure</div>
                    <div class="metric-value">{sys}/{dia} mmHg</div>
                    <div class="metric-zone {zone_cls}">✦ {zone} State</div>
                </div>
                """, unsafe_allow_html=True)
                
        # Draw LDL
        if "ldl" in metrics:
            val = metrics["ldl"]
            zone, zone_cls = ("Normal", "zone-normal") if val < 100 else (("Borderline", "zone-borderline") if val <= 159 else ("High", "zone-danger"))
            with v_col1:
                st.markdown(f"""
                <div class="metric-card-custom">
                    <div class="metric-title">LDL Cholesterol</div>
                    <div class="metric-value">{val} mg/dL</div>
                    <div class="metric-zone {zone_cls}">✦ {zone} Bound</div>
                </div>
                """, unsafe_allow_html=True)
                
        # Draw Hemoglobin
        if "hb" in metrics:
            val = metrics["hb"]
            zone, zone_cls = ("Anemia/Low", "zone-danger") if val < 12.1 else (("Normal", "zone-normal") if val <= 17.2 else ("Elevated", "zone-borderline"))
            with v_col2:
                st.markdown(f"""
                <div class="metric-card-custom">
                    <div class="metric-title">Hemoglobin</div>
                    <div class="metric-value">{val} g/dL</div>
                    <div class="metric-zone {zone_cls}">✦ {zone} Count</div>
                </div>
                """, unsafe_allow_html=True)
    else:
        st.caption("No tabular clinical indicators detected in text. Upload numeric report files to update visualizer.")

    # Results Window
    st.markdown("### 🩺 Clinical Synthesis Output")
    results_placeholder = st.empty()
    results_placeholder.info("System idle. Setup access token, provide patient logs or image scans, and run analysis.")

# =====================================================================
# RETRIEVAL-AUGMENTED PIPELINE INFERENCE EXECUTION
# =====================================================================
if execute_analysis:
    # Validation step 1: HF token check
    if not hf_token:
        st.error("Authentication Error: You must enter a Hugging Face Access Token (`HF_TOKEN`) in the sidebar to authorize requests.")
    
    # Validation step 2: Input check
    elif not input_text.strip() and not uploaded_file:
        st.error("Payload Input Error: You must either provide diagnostic logs in the text area or upload a document/image.")
        
    else:
        # Run execution pipeline
        with st.spinner("Executing serverless RAG chain analysis..."):
            
            # 1. Retrieve guidelines grounding context (RAG Retrieval step)
            retrieved_context = retrieve_guidelines_context(combined_text_for_rag)
            
            # Format Context to prepend to query
            context_formatted = ""
            if retrieved_context:
                context_formatted = (
                    f"=== Ground Truth Clinical Guidelines Reference Context ===\n"
                    f"{retrieved_context}\n"
                    f"===========================================================\n\n"
                )
                
            # 2. Strict system prompt boundary (Prompt engineering directive)
            system_prompt = (
                "You are a specialized clinical AI assistant. Analyze this medical artifact. Instructions: \n"
                "1. Identify the input modality (e.g., Blood Panel, Chest X-ray, Lumbar MRI, Pelvic Ultrasound).\n"
                "2. Highlight out-of-boundary numerical anomalies or physical structural abnormalities.\n"
                "3. Clarify complex definitions for educational use.\n"
                "4. Do NOT prescribe medications or specify exact drug dosages.\n"
                "5. Conclude the response with a bolded safety disclaimer urging immediate professional medical validation."
            )
            
            # Compose Prompt text
            user_prompt = f"{context_formatted}Analyze the following medical artifact and query details:\n\n{combined_text_for_rag if combined_text_for_rag.strip() else '[Image scanned artifact provided]'}"
            
            # 3. Build Hugging Face Inference API Multimodal payload
            messages = [
                {"role": "system", "content": system_prompt}
            ]
            
            if image_base64:
                # Construct multimodal message (OpenAI/HF multimodal compatibility structure)
                messages.append({
                    "role": "user",
                    "content": [
                        {"type": "text", "text": user_prompt},
                        {"type": "image_url", "image_url": {"url": f"data:{mime_type};base64,{image_base64}"}}
                    ]
                })
            else:
                messages.append({
                    "role": "user",
                    "content": user_prompt
                })
                
            headers = {
                "Authorization": f"Bearer {hf_token}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": "Qwen/Qwen2.5-VL-7B-Instruct",
                "messages": messages,
                "temperature": 0.1,
                "max_tokens": 600,
                "parameters": {
                    "temperature": 0.1,
                    "max_new_tokens": 600
                }
            }
            
            # Request execution
            api_url = "https://api-inference.huggingface.co/models/Qwen/Qwen2.5-VL-7B-Instruct/v1/chat/completions"
            
            try:
                try:
                    response = requests.post(api_url, headers=headers, json=payload, timeout=60)
                except (requests.exceptions.SSLError, requests.exceptions.ConnectionError) as conn_err:
                    # Fallback for systems with SSL/TLS handshake or local root certificate errors
                    err_str = str(conn_err)
                    if any(term in err_str.lower() for term in ["ssl", "certificate", "eof"]):
                        import urllib3
                        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
                        response = requests.post(api_url, headers=headers, json=payload, timeout=60, verify=False)
                    else:
                        raise conn_err
                
                # Check response status codes
                if response.status_code == 200:
                    response_json = response.json()
                    ai_response = response_json["choices"][0]["message"]["content"]
                    
                    # Output formatting using markdown callouts
                    results_placeholder.markdown("### Clinician Guidance Summary")
                    
                    # Highlight the medical disclaimer visually
                    disclaimer_pattern = r"(\*\*MEDICAL DISCLAIMER:\*\*.*|\*\*DISCLAIMER:\*\*.*|DISCLAIMER:.*)"
                    disclaimer_match = re.search(disclaimer_pattern, ai_response, re.IGNORECASE)
                    
                    if disclaimer_match:
                        # Extract and place in custom styling container at the bottom
                        clean_response = ai_response[:disclaimer_match.start()].strip()
                        disclaimer_text = disclaimer_match.group(0).strip()
                        
                        st.markdown(clean_response)
                        st.markdown(f"""
                        <div class="disclaimer-box">
                            <strong>{disclaimer_text}</strong>
                        </div>
                        """, unsafe_allow_html=True)
                    else:
                        st.markdown(ai_response)
                        
                    # Print context logs if retrieved
                    if retrieved_context:
                        with st.expander("🔍 View Grounding Retrieval Logs (RAG Context)"):
                            st.text(retrieved_context)
                            
                elif response.status_code == 503:
                    st.info("Model is currently spinning up on serverless clusters. Retrying soon...")
                    st.warning("Hugging Face API reports model loading state. Please wait 15-30 seconds and click Execute again.")
                else:
                    st.error(f"API Connection Error (Code {response.status_code}): {response.text}")
                    
            except requests.exceptions.Timeout:
                st.error("Request Timeout: The serverless inference endpoint took too long to respond. Please verify token and connection state.")
            except Exception as e:
                st.error(f"Execution Error: {str(e)}")
