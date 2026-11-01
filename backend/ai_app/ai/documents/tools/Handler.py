import os
import sys
import pandas as pd
from psycopg2.extras import execute_values
import json
from datetime import datetime

sys.path.append(r'D:\Rushal\VS_code\Python\ProjectIII\backend')
from ai_app.ai.documents.tools.connection import get_db_cursor
from ai_app.ai.utils.embeddings import embed_text_local

# os.chdir(r'D:\Rushal\VS_code\Python\ProjectIII\backend\ai\documents\created_doc')

def see_current_path():
    return {
        'base_path' :  r'backend\ai\documents',
    }

def list_files(filepath):
    print(os.listdir(filepath))

def extract_file(file_paths,base_path=""):
    filepaths = []
    if base_path:
        print("adding base")
        for path in file_paths:
            filepaths.append(base_path+ (path))
    else:
        filepaths = filepaths + file_paths

    datas =[]
    for path in filepaths:
        if path.endswith((".xlsx", ".xls")):  # Without .lower()
            df = pd.read_excel(path)
            datas.append(df)
        elif path.endswith(".csv"):
            df = pd.read_csv(path)
            datas.append(df)
        elif path.endswith(".json"):
            df = pd.read_json(path)
            datas.append(df)
        elif path.endswith(".parquet"):
            df = pd.read_parquet(path)
            datas.append(df)

    return datas

def get_or_create_source(source_name, source_description, cur):
    """Insert source or get existing ID."""
    # Check if source exists
    cur.execute("""
        SELECT id FROM common_document_source 
        WHERE name = %s
    """, (source_name,))
    result = cur.fetchone()
    
    if result:
        return result[0]  # Existing source ID
    else:
        cur.execute("""
            INSERT INTO common_document_source (name, description, created_at)
            VALUES (%s, %s, NOW())
            RETURNING id
        """, (source_name, source_description))
        return cur.fetchone()[0]  # New source ID

def batch_insert_questions(df,source_name,source_description, batch_size=500):
    """
    Insert data into PostgreSQL in batches with proper error handling.
    
    Args:
        df: Pandas DataFrame with columns: question, role, answer, roles, keywords
        batch_size: Number of rows per batch (default: 500)
    """
    # Connect to database
    with get_db_cursor() as cur:
        # Step 1: Get/create source
        source_id = get_or_create_source(
            source_name,
            source_description,
            cur
        )
        print(f"📌 Using source_id: {source_id}")
        
        total_rows = len(df)
        print(f"📊 Total rows to insert: {total_rows}")
        
        # Step 2: Process in batches
        for start_idx in range(0, total_rows, batch_size):
            end_idx = min(start_idx + batch_size, total_rows)
            batch = df.iloc[start_idx:end_idx]
            
            values = []
            for _, row in batch.iterrows():
                # Generate embeddings
                q_emb = embed_text_local(row["question"])
                # a_emb = embed_text_local(row["answer"])
                
                if q_emb is None:
                    print(f"⚠️ Skipping row {_}: embedding failed")
                    continue
                # if q_emb is None or a_emb is None:
                #     print(f"⚠️ Skipping row {_}: embedding failed")
                #     continue
                
                values.append((
                    row["question"],
                    row["answer"],
                    row["role"],
                    row["assigned_experience"],
                    row["difficulty"],
                    json.dumps(row.get("keywords", "")),
                    source_id,  # ← Use the source_id here
                    q_emb,      # question_embedding
                    datetime.now()
                    # a_emb       # answer_embedding
                ))
            
            if values:
                insert_query = """
                    INSERT INTO common_interviewquestions 
                    (question, answer, role, experience, difficulty, keywords, source_id, embedding, created_at)
                    VALUES %s
                """
                execute_values(cur, insert_query, values)
                
                print(f"✅ Inserted batch {start_idx//batch_size + 1}: rows {start_idx}-{end_idx} ({len(values)} records)")
            else:
                print(f"⚠️ Batch {start_idx//batch_size + 1}: no valid records to insert")
        
        print(f"\n🎉 Successfully inserted all rows with source_id: {source_id}")
