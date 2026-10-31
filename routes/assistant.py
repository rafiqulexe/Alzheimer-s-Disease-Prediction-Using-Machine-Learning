# routes/assistant.py
import logging
from datetime import datetime, timezone
from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from bson import ObjectId

from langchain_ollama.llms import OllamaLLM
from langchain_core.prompts import ChatPromptTemplate
from vector import get_retriever

from db import users_col, chats_col
from core.templates import templates
from core.security import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(tags=["assistant"])

chat_template = """
You are an assistant that explains Alzheimer's disease in clear, calm language.
Use the context below plus your own knowledge, but do NOT give medical diagnosis.
Always encourage users to consult a doctor for personal medical decisions.

Context from documents:
{data}

User question:
{question}
"""
prompt = ChatPromptTemplate.from_template(chat_template)

@router.get("/assistant", response_class=HTMLResponse)
async def assistant_page(request: Request):
    user_id, role = get_current_user(request)
    if not user_id:
        return RedirectResponse(url="/login", status_code=302)

    user_email = None
    full_name = None
    u = users_col.find_one({"_id": ObjectId(user_id)})
    if u:
        user_email = u.get("email")
        full_name = u.get("full_name")

    return templates.TemplateResponse(
        "assistant.html",
        {
            "request": request,
            "user_id": user_id,
            "user_email": user_email,
            "full_name": full_name,
            "role": role,
            "user_role": role,
        },
    )

@router.post("/chat")
async def chat_api(request: Request, question: str = Form(...)):
    """
    Receives a user question, retrieves relevant chunks from the PDF via FAISS,
    sends them + question to Ollama, and returns the answer.
    """
    try:
        retriever = get_retriever()
        data_text = ""
        if retriever:
            try:
                docs = retriever.invoke(question)
                if docs:
                    data_text = "\n\n".join(d.page_content for d in docs)
            except Exception as e:
                logger.warning(f"Retriever invocation failed: {e}")

        if not data_text:
            data_text = "General information about Alzheimer's disease diagnosis, support, and clinical care."

        try:
            llm = OllamaLLM(model="llama3.2")
            chat_chain = prompt | llm
            answer = chat_chain.invoke({"data": data_text, "question": question})
            answer_str = str(answer)
        except Exception as ollama_err:
            logger.warning(f"Ollama call failed: {ollama_err}")
            answer_str = (
                "⚠️ Notice: The local AI assistant model (Ollama llama3.2) is currently offline or unreachable. "
                "Please verify that Ollama is running on your machine (`ollama run llama3.2`). "
                "For immediate questions regarding symptoms or medical advice, please consult your physician or neurologist."
            )

        # save chat history in MongoDB
        user_id, _ = get_current_user(request)
        chats_col.insert_one(
            {
                "user_id": ObjectId(user_id) if user_id else None,
                "question": question,
                "answer": answer_str,
                "created_at": datetime.now(timezone.utc),
            }
        )

        return JSONResponse({"answer": answer_str})
    except Exception as e:
        logger.error(f"Unexpected chat error: {e}")
        return JSONResponse(
            {"answer": "⚠️ An unexpected error occurred while processing your message. Please try again later."},
            status_code=500
        )
