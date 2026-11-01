# from backend.ai.utils.embeddings import create_embedding
# from ai.llm import generate_response


# def answer_with_rag(question):
#     query_vector = create_embedding(question)

#     # Search your vector database here
#     context = search_documents(query_vector)

#     prompt = f"""
#     Context:
#     {context}

#     Question:
#     {question}
#     """

#     return generate_response(prompt)