import numpy as np
from datetime import datetime
import json
import sqlite3
from sklearn.metrics.pairwise import cosine_similarity
conn=sqlite3.connect('file_database.db')
c = conn.cursor()   
    
c.execute('''SELECT * FROM files''')
    
   
items=c.fetchall()
conn.close()
file_database = []
for item in items:
       File_database = { "original_name":item[0]
                        , "text_embedding":json.loads(item[1])
                        , "pattern":item[2] 
                        , "file_type":item[3]
                        , "timestamp":item[4]
                        , "download_url":item[5]
                        , "text":item[6]
                     
       }
       file_database.append(File_database)
        



def filter_history_logic(request_data)  : 
    from main import model
    """Filter uploaded files by year, month, day, and category."""
    new_filtered = []    


    
    
   

    if not file_database:
        return {
            "status": "Empty",
            "message": "No files have been uploaded yet."
        }
    
    # Start with all files
    filtered_history = [
    f.copy()
    for f in file_database
]

    # Filter by year 
    if request_data.query_for_year:
        filtered_history = [
            f for f in filtered_history
            if datetime.strptime(
                f["timestamp"],
                "%Y-%m-%d_%H-%M-%S"
            ).year == int(request_data.query_for_year)
        ]

    # Filter by month
    if request_data.query_for_month:
        filtered_history = [
            f for f in filtered_history
            if datetime.strptime(
                f["timestamp"],
                "%Y-%m-%d_%H-%M-%S"
            ).month == int(request_data.query_for_month)
        ]

    # Filter by day
    if request_data.query_for_day:
        filtered_history = [
            f for f in filtered_history
            if datetime.strptime(
                f["timestamp"],
                "%Y-%m-%d_%H-%M-%S"
            ).day == int(request_data.query_for_day)
        ]

    # Filter by category
    
        
    if request_data.query_for_filename:
        filtered_history = [
            f for f in filtered_history
            if f["filename"].lower() == request_data.query_for_filename.lower()
        ]
    
        # Create empty box for surviving files
        
    if not filtered_history:
               return {
                   "status": "Not Found",
                   "message": "No matching files found." 
               }
   
# Encode the user's search ONCE
      # Start with the date/category filtered list
     
    if request_data.query_for_text:


     query_text_embedding = model.embed_documents(
        request_data.query_for_text

    )  
       
    # Go through files one by one
     for f in filtered_history:
        if f.get("text"): 
        # Encode file text
         
        # Compare meanings
         similarity = cosine_similarity(
            [f["text_embedding"]],
            query_text_embedding
        )[0][0]
         
 

         
        # If meanings are close enough
         if similarity  >= 0.40:

            full_text = f["text"]

            search_term = request_data.query_for_text

            start_index = full_text.lower().find(
                search_term.lower()
            )

            if start_index != -1:

                snippet_start = max(
                    0,
                    start_index - 70
                )

                preview_text = (
                    "..."
                    + full_text[
                        snippet_start :
                        snippet_start + 150
                    ]
                    + "..."
                )

            else:
                # Semantic match fallback
                preview_text = (
                    full_text[:150] + "..."
                )

            # Save preview into file result
            f["preview"] = preview_text

            # Keep file
            new_filtered.append(f)

     if not new_filtered:
               return {
                   "status": "Not Found",
                   "message": "No matching files found." 
               }
# Replace old list with surviving files
    new_filtered = filtered_history       
    if request_data.query_for_pattern:
        new_filtered = [
            f for f in new_filtered
            if f["pattern"].lower() == request_data.pattern.lower()
        ]
  # Remove full text to save space
    # Nothing found
    if not new_filtered:
        return {
            "status": "Not Found",
            "message": "No matching files found." 
        }

       

    
    else:
        filtered_results = []
        for f in new_filtered:
         if f.get("text"): 
        
           
          if not f.get("preview") :
           f["new text"] = f["text"][:150] + "..."  
          f.pop("text", None)
          f.pop("text_embedding", None)
          filtered_results.append(f)         
        
        return {
            "status": "Success",
            "matches_found": len(filtered_results),
            "results": filtered_results[:request_data.limit]  # Limit results based on user input
        }
