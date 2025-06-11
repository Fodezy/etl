# File: src/parser/requisite_parser/transformer.py
# This file contains the RequisiteTransformer class.

from lark import Transformer, Token
from typing import Any, List

class RequisiteTransformer(Transformer):
    """
    Transforms the Lark parse tree into a structured JSON object.
    Each method in this class corresponds to a rule in the requisite.lark grammar.
    """
    def __init__(self, debug: bool = False):
        self.debug = debug
        super().__init__()

    # --- Rule Methods ---

    def start(self, items: List[Any]) -> Any:
        return items[0]

    def logical_or(self, items: List[Any]) -> Any:
        if len(items) == 1:
            return items[0]
        return {"type": "OR", "operands": items}

    def logical_and(self, items: List[Any]) -> Any:
        if len(items) == 1:
            return items[0]
        return {"type": "AND", "operands": items}
    
    def atomic_expression(self, items: List[Any]) -> Any:
        return items[0]

    def group(self, items: List[Any]) -> Any:
        """
        Handles a grouped expression from the 'group' alias. It just returns
        the content of the group, effectively removing the parentheses
        from the final structure.
        """
        return items[0]

    def course_code(self, items: List[Token]) -> dict:
        course_token = items[0]
        return {
            "type": "COURSE",
            "code": str(course_token)
        }
