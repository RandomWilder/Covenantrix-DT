# OCR PDF Processing Fix - Technical Brief

## Problem Statement

**Scanned PDFs return 0 text extracted** from Google Vision API.

**Root Cause:** Raw PDF bytes are being sent to Google Vision's `/images:annotate` endpoint, which only accepts image formats (PNG, JPG, etc.). The API silently fails and returns empty text.

---

## Current State

### Files Involved
- `backend/infrastructure/external/google_vision_ocr.py` - OCR processing logic
- `backend/infrastructure/external/google_vision_client.py` - Google Vision API client
- `backend/requirements.txt` - Python dependencies

### Current Dependencies
```txt
PyPDF2>=3.0.0           # Text extraction (not rendering)
Pillow>=10.0.0          # Image processing
pytesseract>=0.3.10     # Legacy OCR (not used for Google Vision)
google-cloud-vision>=3.4.0
```

### Current Flow (BROKEN)
```
PDF Upload → google_vision_ocr._process_pdf() 
→ client.detect_text(pdf_content=raw_pdf_bytes) 
→ /images:annotate endpoint 
→ Returns empty (PDFs not supported)
```

---

## Required Changes

### 1. Add PDF-to-Image Dependency

**File:** `backend/requirements.txt`

**Add:**
```txt
PyMuPDF==1.24.0  # PDF rendering to images (pure Python, cross-platform)
```

**Why PyMuPDF:**
- ✅ Pure Python (no system dependencies like Poppler)
- ✅ Cross-platform (Windows, Mac, Linux)
- ✅ Fast rendering
- ✅ Production-ready

**❌ DO NOT USE:**
- `pdf2image` - Requires system-level Poppler installation (platform-specific)
- Any dependency requiring external system libraries

---

### 2. Update PDF Processing Logic

**File:** `backend/infrastructure/external/google_vision_ocr.py`

**Method:** `_process_pdf(self, pdf_content: bytes, filename: str)`

**Current Issue:**
```python
# WRONG: Sends raw PDF bytes to image endpoint
response = await client.detect_text(
    image_content=pdf_content,  # PDF bytes!
    use_document_detection=True
)
```

**Required Fix:**
```python
# CORRECT: Convert PDF to images first
import fitz  # PyMuPDF
from PIL import Image

# 1. Open PDF with PyMuPDF
pdf_doc = fitz.open(stream=pdf_content, filetype="pdf")

# 2. Render each page to image (300 DPI)
for page_num in range(len(pdf_doc)):
    page = pdf_doc[page_num]
    mat = fitz.Matrix(300/72, 300/72)
    pix = page.get_pixmap(matrix=mat)
    img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
    
    # 3. Convert to PNG bytes
    img_bytes = ... # BytesIO conversion
    
    # 4. Send image to Vision API
    response = await client.detect_text(image_content=img_bytes)
```

**Key Changes:**
- Convert PDF → Images (one per page)
- Process each page separately
- Combine results from all pages
- Use 300 DPI for quality OCR

---

### 3. Improve Error Logging

**File:** `backend/infrastructure/external/google_vision_client.py`

**Method:** `_make_api_request()`

**Add logging on API errors:**
```python
elif response.status == 400:
    error_data = await response.json()
    self.logger.error(f"Google Vision API 400: {error_data}")  # ADD THIS
    raise GoogleVisionAPIError(...)
```

**Purpose:** See what Google Vision returns when requests fail.

---

### 4. Lower Validation Threshold

**File:** `backend/infrastructure/external/google_vision_ocr.py`

**Change:** `self.min_char_count = 5` → `self.min_char_count = 1`

**Reason:** Minimum of 5 characters is too strict for short documents.

---

## Implementation Summary

| Component | Action | File |
|-----------|--------|------|
| **Dependencies** | Add `PyMuPDF==1.24.0` | `requirements.txt` |
| **PDF Processing** | Convert PDF→Images before OCR | `google_vision_ocr.py` |
| **Error Logging** | Log API error responses | `google_vision_client.py` |
| **Validation** | Lower min char threshold to 1 | `google_vision_ocr.py` |

---

## What to Avoid

❌ **DO NOT use pdf2image** - Requires Poppler (system dependency)  
❌ **DO NOT send raw PDF bytes to `/images:annotate`** - Won't work  
❌ **DO NOT use `/files:annotate`** - Async API, different response structure  
❌ **DO NOT add platform-specific dependencies** - Violates architecture requirements

---

## Expected Outcome

**Before Fix:**
```
Google Vision response: text_length=0, confidence=0.0
No text extracted from חוזה עלם.pdf
```

**After Fix:**
```
Converting PDF to images: חוזה עלם.pdf
Converted 2 pages
Page 1: extracted 1247 chars
Page 2: extracted 983 chars
PDF processing complete: 2230 chars, 0.87 confidence
```

---

## Testing

1. Install: `pip install PyMuPDF==1.24.0`
2. Restart backend
3. Upload Hebrew scanned PDF
4. Verify logs show page-by-page processing
5. Confirm text extraction > 0 characters

---

## Technical Context

**Google Vision API Endpoints:**
- `/images:annotate` - Sync, accepts images only (PNG, JPG, etc.)
- `/files:annotate` - Async batch, complex response handling

**Our Approach:**
- Use `/images:annotate` (simpler, synchronous)
- Pre-convert PDFs to images with PyMuPDF
- Process each page separately
- Combine results

**Time Estimate:** 2-3 hours implementation + testing