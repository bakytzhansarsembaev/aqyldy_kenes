from pydantic import ValidationError, BaseModel
from typing import Optional, Any, Dict, List
# class User:
#     def __init__(self):
#         pass


class User(BaseModel):
    user_id: str

    # результат классификации
    intent: str | None = None
    subintent: str | None = None

    # язык ученика
    language: str = "kaz"

    # contexts
    context: str
    full_context: str
    session_context: str

    def set_class(self, _intent, _subintent):
        self.intent = _intent
        self.subintent = _subintent

    def set_language(self, _language):
        self.language = _language

    def set_context(self, _context):
        self.context = _context

    def set_full_context(self, _full_context):
        self.full_context = _full_context

    def set_session_context(self, _session_context):
        self.session_context = _session_context
