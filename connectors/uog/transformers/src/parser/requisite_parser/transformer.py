# File: src/parser/requisite_parser/transformer.py
# This file contains the RequisiteTransformer class.

from lark import Transformer, Token
from typing import Any, List

class RequisiteTransformer(Transformer):
    """
    Transforms the Lark parse tree into a structured JSON object.
    Each method in this class corresponds to an alias or rule in the requisite.lark grammar.
    """
    def __init__(self, debug: bool = False):
        self.debug = debug
        super().__init__()

    # --- Alias Methods ---

    def create_or(self, items: List[Any]) -> Any:
        if len(items) == 1:
            return items[0]
        return {"type": "OR", "operands": items}

    def create_and(self, items: List[Any]) -> Any:
        if len(items) == 1:
            return items[0]
        return {"type": "AND", "operands": items}

    def create_n_of(self, items: List[Any]) -> dict:
        count = int(items[0].value)
        choices = items[1]
        return {"type": "N_OF", "count": count, "operands": choices}

    def to_course_obj(self, items: List[Token]) -> dict:
        course_token = items[0]
        return {
            "type": "COURSE",
            "code": str(course_token)
        }

    # --- Rule Methods (for rules without aliases) ---

    def start(self, items: List[Any]) -> Any:
        return items[0]
    
    def and_or_nof_expression(self, items: List[Any]) -> Any:
        return items[0]

    def n_of_choice_list(self, items: List[Any]) -> List[Any]:
        return items
    
    def simple_atom(self, items: List[Any]) -> Any:
        return items[0]
    
    def group(self, items: List[Any]) -> Any:
        return items[0]
