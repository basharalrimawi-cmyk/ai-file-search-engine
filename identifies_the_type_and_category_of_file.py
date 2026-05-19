import shutil
from fastapi.responses import FileResponse
from fastapi import FastAPI, UploadFile, File
from sentence_transformers import  util
from pydantic import BaseModel, Field
from Model import model
import magic
from the_conditions import extract_text_universally
from pathlib import Path 
from datetime import datetime
from Model import file_database
from the_history import filter_history_logic  # PyMuPDF for PDF extraction
class ClassificationResponse(BaseModel):
    category_path: str
    confidence: float
app = FastAPI()



taxonomy_mapping = {
    "Administrative, Executive Affairs, General Secretariat, Official Correspondence, internal memos": "Administrative",
    "Archival, Records Management, Historical Records, Permanent Archives, long-term record keeping": "Archival",
    "Financial, Accounts Payable, Fiscal Records, Accounting, invoices, budgets, payroll, receipts": "Financial"
}

categories = list(taxonomy_mapping.keys())
category_embeddings = model.encode(categories)
pattern_mapping = {
    "Contract, legal agreement, terms and conditions, signed binding document, obligations": "Contract",
    "Invoice, bill, receipt, purchase order, total amount due, payment request": "Invoice",
    "Report, analysis, summary, status update, research findings, formal review": "Report",
    "Form, application, questionnaire, fillable fields, survey, user input": "Form",
    "Correspondence, email, letter, memo, communication, direct message": "Correspondence",
    "Meeting minutes, agenda, discussion points, action items, board meeting, attendees": "Meeting Minutes",
    "Policy, procedure, guideline, rule, compliance manual, employee handbook, instructions": "Policy/Procedure",
    "Resume, curriculum vitae, CV, applicant profile, cover letter, work experience, education": "Resume/CV"
}
pattern_keys = list(pattern_mapping.keys())
pattern_embeddings = model.encode(pattern_keys)



def classify_document(document_text: str, file_type: str):
   
    document_embedding = model.encode(document_text)
    
    
    scores = util.cos_sim(document_embedding, category_embeddings)[0]
    

    
    best_score_index = scores.argmax().item()
    winning_category = categories[best_score_index]
    confidence = scores[best_score_index].item()
    final_category = taxonomy_mapping[winning_category]
 
    if confidence < 0.50:
        final_category = "Uncategorized / Needs Human Review"
    final_confidence = round(confidence * 100, 2)

    pattern_scores = util.cos_sim(document_embedding, pattern_embeddings)[0]
    pattern_best_index = pattern_scores.argmax().item()
    
    pattern_winning_key = pattern_keys[pattern_best_index]
    
    final_pattern = pattern_mapping[pattern_winning_key] 
    
    
    return {
        "category_path": final_category,
        "content_pattern": final_pattern,
        "confidence": f"{final_confidence}%", # Adds the clean percentage sign
        "file_type": file_type
    }

UPLOAD_DIR = Path("stored_files")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
file_database = []
download_url = ""

@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    
    content_bytes = await file.read()
    file.file.seek(0)

     
    original_name = Path(file.filename).name
    # 2. Make it unique (Add a timestamp so we don't overwrite)
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    unique_filename = f"{timestamp}_{original_name}"
    
    file_path = UPLOAD_DIR / unique_filename # Using / operator is much cleaner!

    # 3. Save the file
    with file_path.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    file_type = magic.from_buffer(content_bytes, mime=True)
     
   
    download_url = f"http://127.0.0.1:8000/download/{unique_filename}"
    
   
    

    

    
    
    text = await extract_text_universally(content_bytes, file_type)
    
    classification = classify_document(text, file_type)
    file_info = {
        "original_name": original_name,
        "text": text,
        "content_pattern": classification["content_pattern"],
        "file_type": file_type,
        "timestamp": timestamp,
        "download_url": download_url
    }

    file_database.append(file_info)
    return classification  



@app.get("/download/{filename}")
async def download_file(filename: str):

    file_path = UPLOAD_DIR / filename

    return FileResponse(file_path)

class SearchRequest(BaseModel):
    query_for_text: str | None  = Field(
        None,
        example="")
    query_for_year: str | None =  Field(
        None, example="")
    query_for_month: str | None = Field(
        None, example="")
    query_for_day: str  | None  = Field(
        None, example="")
    query_for_filename:str | None  = Field(
        None, example="")
    query_for_pattern:str  | None  = Field(
        None, example="")
    limit: int = Field(
        3,
        ge=1,
        le=50
    )
 

   
@app.post("/search")
async def search(request: SearchRequest):  
    
   
    final_results = filter_history_logic(request)

    
    
    return final_results



 

















 





