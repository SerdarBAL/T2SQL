"""REST endpoints for the conversation-history sidebar.

  GET    /api/conversations        list (id, title, updated_at)
  POST   /api/conversations        create -> {id}
  GET    /api/conversations/{id}   full thread (with messages)
  PUT    /api/conversations/{id}   update title and/or messages
  DELETE /api/conversations/{id}   remove
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.db import conversations as store

router = APIRouter(prefix="/api/conversations")


class CreateConversation(BaseModel):
    title: str
    messages: list = []


class UpdateConversation(BaseModel):
    title: str | None = None
    messages: list | None = None


@router.get("")
def list_all() -> list[dict]:
    return store.list_conversations()


@router.post("")
def create(body: CreateConversation) -> dict:
    conversation_id = store.create_conversation(body.title, body.messages)
    return {"id": conversation_id}


@router.get("/{conversation_id}")
def get_one(conversation_id: str) -> dict:
    conversation = store.get_conversation(conversation_id)
    if conversation is None:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return conversation


@router.put("/{conversation_id}")
def update(conversation_id: str, body: UpdateConversation) -> dict:
    ok = store.update_conversation(conversation_id, body.title, body.messages)
    if not ok:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return {"ok": True}


@router.delete("/{conversation_id}")
def delete(conversation_id: str) -> dict:
    ok = store.delete_conversation(conversation_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return {"ok": True}
