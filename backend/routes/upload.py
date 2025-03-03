from fastapi import APIRouter, UploadFile, HTTPException
import fitz  # PyMuPDF
import os
from typing import List
import tempfile

router = APIRouter()

def split_text_into_segments(text: str, words_per_segment: int = 50) -> List[str]:
    """Split text into segments of approximately words_per_segment words."""
    words = text.split()
    segments = []
    
    for i in range(0, len(words), words_per_segment):
        segment = " ".join(words[i:i + words_per_segment])
        segments.append(segment)
    
    return segments

@router.post("/api/upload")
async def upload_pdf(file: UploadFile):
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")
    
    try:
        # Create a temporary file to store the uploaded PDF
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_pdf:
            content = await file.read()
            temp_pdf.write(content)
            temp_pdf.flush()
            
            # Open the PDF with PyMuPDF
            doc = fitz.open(temp_pdf.name)
            text_content = []
            
            # Extract text from each page
            for page in doc:
                text_content.append(page.get_text())
            
            # Close the document
            doc.close()
            
            # Remove temporary file
            os.unlink(temp_pdf.name)
            
            # Combine all text and split into segments
            full_text = " ".join(text_content)
            segments = split_text_into_segments(full_text)
            
            return {
                "filename": file.filename,
                "num_segments": len(segments),
                "segments": segments
            }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing PDF: {str(e)}")
