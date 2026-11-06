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


def _parse_jsonish(value, default):
    """Parse a value that might be a real list/dict or a JSON-ish string."""
    if value is None:
        return default
    if isinstance(value, float) and pd.isna(value):
        return default
    if isinstance(value, (list, dict)):
        return value
    if isinstance(value, str):
        s = value.strip()
        if not s:
            return default
        try:
            return json.loads(s.replace("'", '"'))
        except Exception:
            return default
    return default


def batch_insert_questions(df, source_name, source_description, batch_size=500):
    """
    Insert pre-embedded question rows into PostgreSQL in batches.

    Expected df columns:
        question, answer, role, experience, difficulty, keywords,
        categories, weights, embedding   ← embedding must already exist
    """
    with get_db_cursor() as cur:
        source_id = get_or_create_source(source_name, source_description, cur)
        print(f"📌 Using source_id: {source_id}")

        total_rows = len(df)
        print(f"📊 Total rows: {total_rows}")

        inserted_total = 0
        skipped_total  = 0

        for start_idx in range(0, total_rows, batch_size):
            end_idx = min(start_idx + batch_size, total_rows)
            batch = df.iloc[start_idx:end_idx]

            values = []

            for _, row in batch.iterrows():
                # ---------- embedding (use existing, do NOT re-embed) ----------
                q_emb = row.get("embedding")

                if q_emb is None or (isinstance(q_emb, float) and pd.isna(q_emb)):
                    print(f"⚠️ Skip row {_}: missing embedding")
                    skipped_total += 1
                    continue

                if isinstance(q_emb, str):
                    try:
                        q_emb = json.loads(q_emb)
                    except Exception:
                        print(f"⚠️ Skip row {_}: bad embedding string")
                        skipped_total += 1
                        continue

                if not isinstance(q_emb, list) or len(q_emb) == 0:
                    print(f"⚠️ Skip row {_}: embedding not a list")
                    skipped_total += 1
                    continue

                # ---------- categories (TEXT[]) ----------
                cats = _parse_jsonish(row.get("categories"), [])
                if not isinstance(cats, list):
                    cats = [str(cats)]

                # ---------- weights (JSONB) ----------
                wts = _parse_jsonish(row.get("weights"), [])
                if not isinstance(wts, list):
                    wts = []

                # ---------- keywords ----------
                kws = row.get("keywords", "")
                if isinstance(kws, (list, dict)):
                    kws = json.dumps(kws)
                elif kws is None or (isinstance(kws, float) and pd.isna(kws)):
                    kws = ""

                values.append((
                    row["question"],
                    row["answer"],
                    row["role"],
                    row["experience"],
                    row["difficulty"],
                    kws,
                    source_id,
                    q_emb,              # list[float] → vector(768)
                    cats,               # list[str]   → TEXT[]
                    json.dumps(wts),    # str         → JSONB
                    datetime.now(),
                ))

            if not values:
                print(f"⚠️ Batch {start_idx//batch_size + 1}: nothing to insert")
                continue

            insert_query = """
                INSERT INTO common_interviewquestions
                    (question, answer, role, experience, difficulty,
                     keywords, source_id, embedding,
                     categories, weights, created_at)
                VALUES %s
            """

            try:
                execute_values(cur, insert_query, values)
                inserted_total += len(values)
                print(f"✅ Batch {start_idx//batch_size + 1}: "
                      f"{len(values)} inserted ({start_idx}–{end_idx})")
            except Exception as e:
                print(f"❌ Batch {start_idx//batch_size + 1} failed: {e}")
                raise

        print(f"\n🎉 Done. inserted={inserted_total}, skipped={skipped_total}, "
              f"source_id={source_id}")
