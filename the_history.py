from datetime import datetime
from sentence_transformers import util


def filter_history_logic(request_data):
    from identifies_the_type_and_category_of_file import file_database
    from Model import model
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
        
       
# Encode the user's search ONCE
      # Start with the date/category filtered list

    if request_data.query_for_text:

       query_text_embedding = model.encode(
        request_data.query_for_text
    )

    # Go through files one by one
       for f in filtered_history:

        # Encode file text
         text_embedding = model.encode(f["text"])

        # Compare meanings
         similarity = util.cos_sim(
            text_embedding,
            query_text_embedding
        )[0][0]

        # If meanings are close enough
         if similarity >= 0.40:

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

     # Start with the date/category filtered list
    new_filtered = filtered_history   
# Replace old list with surviving files
           
    if request_data.query_for_pattern:
        new_filtered = [
            f for f in new_filtered
            if f["pattern"].lower() == request_data.pattern.lower()
        ]

    for f in new_filtered:
        f["new text"] = f["text"][:150] + "..."  
        del f["text"]  # Remove full text to save space
    # Nothing found
    if not new_filtered:
        return {
            "status": "Not Found",
            "message": "No matching files found."
        }

       

    
    else:
        return {
            "status": "Success",
            "matches_found": len(new_filtered),
            "results": new_filtered[:request_data.limit]  # Limit results based on user input
        }
