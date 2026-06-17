# ClinicalRAG-Hub (MedClarify Engine)

> **Universal Multimodal Serverless Medical RAG Pipeline**  
> An elite, production-grade Clinical Decision Support System (CDSS) designed to securely ingest, parse, and analyze raw alphanumeric laboratory panels, PDF diagnostic reports, and high-resolution visual medical scans (X-Rays, MRIs, Ultrasounds, and Echocardiograms) within free-tier compute limitations without compromising safety, accuracy, or cost.

---

## 1. Project Title & Elevator Pitch

**ClinicalRAG-Hub (MedClarify Engine)** is a zero-local-VRAM, serverless Retrieval-Augmented Generation (RAG) system that processes both raw patient text logs and medical imagery using a hybrid multimodal pipeline. By splitting execution between a lightweight CPU-only Streamlit container (frontend router) and Hugging Face’s serverless inference clusters hosting the state-of-the-art `Qwen2.5-VL-7B-Instruct` Vision-Language Model, the platform delivers real-time clinical anomaly highlighting, terminology explanation, and guideline grounding—without local memory overhead or hallucinating dangerous medical instructions.

---

## 2. Core Problems Solved

### A. The Medical Hallucination Dilemma
Standard Large Language Models (LLMs) are optimized for conversational plausibility, which leads to **hallucinations**—a catastrophic failure state in clinical medicine. A general LLM might invent incorrect normal reference ranges or generate toxic, unauthorized medication dosages when analyzing a report. 
* **The Solution:** Our architecture strictly clamps the LLM's decoding parameters (`temperature=0.1`) to suppress creative sampling. Additionally, we use a custom **RAG ground-truth matching layer** that intercepts user inputs, fetches official reference rules from clinical guidelines, and injects them as immutable grounding context, enforcing a strict boundary for the model.

### B. The Compute Cost Barrier
Local deployment of a Vision-Language Model (VLM) capable of clinical reasoning requires a minimum of **16GB to 24GB of dedicated VRAM** for comfortable FP16/INT8 execution. On free hosting platforms like Streamlit Cloud, container memory is restricted to 1GB, resulting in immediate Out-Of-Memory (OOM) kernel panics upon loading model weights.
* **The Solution:** We implement **Serverless Engine Splitting**. The local container acts solely as a zero-weight orchestrator handling UI state, file uploads, PDF text extraction, and rule indexing. The heavy tensor computation is offloaded via encrypted HTTPS payloads to the Hugging Face Free Serverless Inference API, costing $0 in local hosting and hardware overhead.

### C. The Layout Distortion Problem
Traditional Optical Character Recognition (OCR) pipelines convert multi-column blood report tables, structural reports, and lab metrics into flat string text. This process completely disrupts horizontal alignments, merging independent values (e.g., matching the wrong metric name to a neighboring numerical result) and corrupting downstream analysis.
* **The Solution:** By migrating to a **Vision-Language Model (VLM)** like Qwen2.5-VL, the system treats raw images directly as **patch embeddings** (visual tokens). The model preserves spatial relations, columns, grids, and visual scan components natively without relying on error-prone heuristic text alignment tools.

---

## 3. System Architecture Diagram

```text
[User Upload]
      │ (Text findings, Lab PDFs, or Medical Scan PNG/JPG)
      ▼
[Streamlit Frontend Router] 
      │
      ├─► [Modality Routing] ──► If Image Scan ──► [Base64 Encoder] ──────────────┐
      │                                                                           │
      └─► If PDF / Text Box ──► [PDF/Text Parser] ──► [Extracted Alphanumeric]   │
                                                            │                     │
                                                            ▼                     ▼
[In-Memory Vector Search (FAISS)] ◄─────────────────────────┘            [Payload Builder]
      │                                                                           │
      ├── (Query Embeddings via Sentence-Transformers)                            │
      ▼                                                                           │
[Ground Truth Guidelines Retrieval] ──────────────────────────────────────────────┤
                                                                                  ▼
                                                                     [HTTPS Payload Assembly]
                                                                        (T=0.1, Token Auth)
                                                                                  │
                                                                                  ▼
                                                                     [HF Serverless API Gateway]
                                                                                  │
                                                                                  ▼
                                                                    [Qwen/Qwen2.5-VL-7B-Instruct]
                                                                        (Remote Inference Engine)
                                                                                  │
                                                                                  ▼
                                                                     [Streamlit UI Display]
                                                                     (Synthesis & Disclaimer)
```

---

## 4. Technical Stack Justification (The "Why" Matrix)

| Dimension / Core Decision | Selected Architecture | Alternative Evaluated | Trade-Off & Justification |
| :--- | :--- | :--- | :--- |
| **Model Selection** | **Qwen2.5-VL-7B-Instruct** | BioMistral-7B | **Multimodal Versatility:** BioMistral is strictly text-based and cannot read visual scans (X-Rays, MRIs) or OCR images. Qwen2.5-VL accepts both visual (via patch embeddings) and textual inputs, permitting universal ingestion in a single model call. |
| **Execution Layer** | **Serverless Inference API** (Hugging Face) | Local CUDA Pipeline | **Zero-Memory Constraint:** Local execution of a 7B model requires 16GB+ VRAM, triggering Out-of-Memory crashes on free containers. Serverless offloads 100% of compute to remote endpoints, running the frontend at 0MB local GPU usage. |
| **Vector Indexing** | **FAISS (In-Memory)** | Cloud Vector DB (Pinecone/Milvus) | **Latency & Cost Efficiency:** Cloud databases add network latency, cold starts, and cost. For clinical guidelines (<100KB), FAISS indexes and matches documents in RAM in <1ms without database subscription dependencies. |

---

## 5. Critical Prompt Engineering & Safety Guardrails

The application secures safety boundaries by hardcoding a custom **System Prompt Boundary** and formatting response components post-generation:

### A. The System Prompt Boundary (Injected into API Payload)
```python
system_prompt = (
    "You are a specialized clinical AI assistant. Analyze this medical artifact. Instructions: \n"
    "1. Identify the input modality (e.g., Blood Panel, Chest X-ray, Lumbar MRI, Pelvic Ultrasound).\n"
    "2. Highlight out-of-boundary numerical anomalies or physical structural abnormalities.\n"
    "3. Clarify complex definitions for educational use.\n"
    "4. Do NOT prescribe medications or specify exact drug dosages.\n"
    "5. Conclude the response with a bolded safety disclaimer urging immediate professional medical validation."
)
```

### B. Safety Parameters Clamping
To enforce deterministic clinical evaluations, parameters are tightly restricted during the API request:
*   `temperature` is set to `0.1` to prevent semantic deviation or creative clinical reasoning.
*   `max_new_tokens` is bounded to `600` to prevent infinite generation loops and conserve token bandwidth.

### C. Regex-Based Post-Extraction Guardrail
To ensure the safety disclaimer is prominently highlighted, a post-processing step separates the LLM output text and isolates the disclaimer:
```python
# Highlight the medical disclaimer visually in a styled HTML block
disclaimer_pattern = r"(\*\*MEDICAL DISCLAIMER:\*\*.*|\*\*DISCLAIMER:\*\*.*|DISCLAIMER:.*)"
disclaimer_match = re.search(disclaimer_pattern, ai_response, re.IGNORECASE)
```
If matched, the disclaimer is extracted from the main response string and rendered inside a custom red-bordered CSS card (`rgba(239, 68, 68, 0.08)`) with a left border highlight to catch user attention.

---

## 6. Placement Interview Questions & Answers

### Q1: The Hugging Face serverless API is free but prone to HTTP 503 errors (Model loading). How does your code handle this state dynamically without losing user files or context?
> **Answer:** The application request layer intercepts HTTP status code `503` specifically. Instead of throwing a stack trace or displaying a blank screen, it displays an informative Streamlit warning alert: `"Model is currently spinning up on serverless clusters. Retrying soon..."` This notifies the user that the remote model is in a cold-start state and is being loaded into remote VRAM. 
> 
> Because we decouple file parsing and file reading from the execution call, the uploaded file and extracted text are safely cached in Streamlit's UI session variables. The user can simply click the analysis button again 15 seconds later to resume the handshake once the weights are initialized.

### Q2: How do you address patient data privacy (HIPAA / DPDP compliance) when transferring sensitive medical files and scans through a public serverless API endpoint?
> **Answer:** In a real-world enterprise setting, three architectural guardrails must be implemented to achieve HIPAA/DPDP compliance:
> 1. **Client-Side De-identification (NER Redaction):** Before compiling the text payload, run a local Named Entity Recognition (NER) pipeline (such as spaCy’s clinical model `en_core_sci_sm`) to redact Protected Health Information (PHI) like patient names, addresses, IDs, and dates, replacement with placeholders in local memory.
> 2. **Zero-Data-Retention (ZDR) Endpoint Contracts:** Ensure that the API token used links to a private, enterprise-level Hugging Face endpoint rather than the public free tier. These endpoints guarantee that input payloads are stored exclusively in temporary volatile GPU memory and never logged, cached, or written to disk.
> 3. **Encrypted Transport Routing:** Enforce standard TLS 1.3 encryption on all outgoing API HTTPS requests to block middleman interception of the Base64-encoded image payloads.

### Q3: Medical reports are full of specialized acronyms (e.g., "Hb", "BP", "HDL"). How would you use a LangChain `EnsembleRetriever` combining FAISS and BM25 to fix out-of-vocabulary acronym lookups that dense semantic vector search might fail to retrieve?
> **Answer:** Dense vector retrievers (like FAISS using embedding models) capture semantic proximity but can fail on exact, short, out-of-vocabulary medical abbreviations or codes because the embeddings of short acronyms like `BP` or `Hb` might project close to unrelated concepts.
> 
> To solve this, we construct a hybrid retrieval pipeline using LangChain's `EnsembleRetriever`:
> 1. **Dense Channel:** We instantiate a `FAISS` vector retriever utilizing `all-MiniLM-L6-v2` embeddings to retrieve documents based on semantic context (e.g., mapping "high sugar" to "diabetes guidelines").
> 2. **Sparse Channel:** We instantiate a `BM25Retriever` indexed on the same document chunks. BM25 performs term-frequency keyword matching, scoring exact keyword overlap.
> 3. **RRF (Reciprocal Rank Fusion):** We combine both retrievers under an `EnsembleRetriever` with weights set to `[0.5, 0.5]`:
>    ```python
>    ensemble_retriever = EnsembleRetriever(
>        retrievers=[bm25_retriever, faiss_retriever],
>        weights=[0.5, 0.5]
>    )
>    ```
> This ensures that if the patient record contains a strict keyword search like `BP` or `HbA1c`, the sparse channel ranks the exact matching guidelines at the top, while the dense channel ensures broad conceptual grounding is also injected, resolving abbreviation lookup errors.
