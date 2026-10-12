import json
import shutil
from dotenv import load_dotenv
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from fastapi.responses import FileResponse
from fastapi import FastAPI, UploadFile, File
from pydantic import BaseModel, Field
import magic
from sklearn.metrics.pairwise import cosine_similarity
from the_conditions import extract_text_universally
from pathlib import Path 
from datetime import datetime
from the_history import filter_history_logic  # for the data time
import sqlite3
from langchain_google_genai import GoogleGenerativeAIEmbeddings
load_dotenv()
model = GoogleGenerativeAIEmbeddings(
    model="gemini-embedding-2",
  
)
class ClassificationResponse(BaseModel):
    category_path: str
    confidence: float



app = FastAPI()
api_key = "your_api_key_here"  # Replace with your actual API key
conn=sqlite3.connect('file_database.db')
c = conn.cursor()


taxonomy_mapping = {
    "Legal and compliance documents, contracts, NDAs, regulatory filings, terms and conditions, legal agreements": "Legal & Compliance",
    "Administrative and operations records, internal memos, meeting minutes, company policies, general correspondence, status reports": "Administrative & Operations",
    "Financial and accounting documents, invoices, payroll, budgets, tax records, purchase orders, receipts": "Financial & Accounting",
    "Human resources and recruitment records, resumes, CVs, cover letters, job applications, onboarding forms, employee files": "Human Resources & Recruitment"
}
categories = list(taxonomy_mapping.keys())
category_embeddings = model.embed_documents(categories)
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
pattern_embeddings = model.embed_documents(pattern_keys)


def classify_document(document_text: str, file_type: str):
   
   document_embedding = model.embed_documents([document_text])

   scores = cosine_similarity(document_embedding, category_embeddings)[0]

   best_score_index = scores.argmax()
   winning_category = categories[best_score_index]
   confidence = scores[best_score_index]
   final_category = taxonomy_mapping[winning_category]

   if confidence < 0.50:
    final_category = "Uncategorized / Needs Human Review"

   final_confidence = round(confidence * 100, 2)

   pattern_scores = cosine_similarity(document_embedding, pattern_embeddings)[0]
   pattern_best_index = pattern_scores.argmax()

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
    text_embedding = model.embed_documents([text])[0]
    embedding_json = json.dumps(text_embedding)
    classification = classify_document(text, file_type)
    c.execute('''CREATE TABLE IF NOT EXISTS files (original_name TEXT, text_embedding TEXT, content_pattern TEXT, file_type TEXT, timestamp TEXT, download_url TEXT)''')
    conn.commit()
    c.execute('''INSERT INTO files (original_name, text_embedding, content_pattern, file_type, timestamp, download_url, text) VALUES (?, ?, ?, ?, ?, ?, ?)''',
     (original_name, embedding_json, classification["content_pattern"], file_type, timestamp, download_url, text))
    conn.commit()
    
    
    return classification

@app.get("/download/{filename}")
async def download_file(filename: str):

    file_path = UPLOAD_DIR / filename

    return FileResponse(file_path)

class SearchRequest(BaseModel):
    query_for_text: str | None = Field(
        None,
        json_schema_extra={"example": ""}
    )

    query_for_year: str | None = Field(
        None,
        json_schema_extra={"example": ""}
    )

    query_for_month: str | None = Field(
        None,
        json_schema_extra={"example": ""}
    )

    query_for_day: str | None = Field(
        None,
        json_schema_extra={"example": ""}
    )

    query_for_filename: str | None = Field(
        None,
        json_schema_extra={"example": ""}
    )

    query_for_pattern: str | None = Field(
        None,
        json_schema_extra={"example": ""}
    )

    limit: int = Field(
        3,
        ge=1,
        le=50
    ) 

   
@app.post("/search")
async def search(request: SearchRequest):  
    
   
    final_results = filter_history_logic(request)

    
    
    return final_results



















 





