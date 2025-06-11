# File: tests/test_parser.py
# Unit tests for the prerequisite parsing system.

import pytest
import sys
import os
from typing import Optional, List, Dict, Any

# --- PATH CORRECTION LOGIC ---
script_dir = os.path.dirname(__file__)
project_root = os.path.abspath(os.path.join(script_dir, '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.parse_prereq import parse_prereq

# --- SPRINT 1 & 2 TESTS (Passing) ---

def test_no_requisites():
    assert parse_prereq(raw_text="None")[0]["type"] == "NO_REQUISITES"

def test_semicolon_split():
    test_string = "CIS*1910; CIS*2500"
    result = parse_prereq(test_string)
    assert len(result) == 2
    assert result[0].get("type") == "COURSE"
    assert result[1].get("type") == "COURSE"

def test_single_course_code():
    test_string = "CIS*2500"
    result = parse_prereq(test_string)
    assert result[0].get("type") == "COURSE"
    assert result[0].get("code") == "CIS*2500"

def test_parse_error_for_invalid_string():
    test_string = "This is not valid"
    result = parse_prereq(test_string)
    assert result[0].get("type") == "PARSE_ERROR"

def test_trailing_comment_cleanup():
    test_string = "CIS*1910 - Must be completed prior to taking this course."
    result = parse_prereq(test_string)
    assert result[0].get("type") == "COURSE"
    assert result[0].get("code") == "CIS*1910"

# --- SPRINT 3 TESTS (New) ---

def test_sprint3_logical_or():
    """
    Tests a simple OR expression between two courses.
    """
    test_string = "CIS*1910 OR CIS*2500"
    result = parse_prereq(test_string)[0]

    assert result["type"] == "OR"
    assert len(result["operands"]) == 2
    assert result["operands"][0]["type"] == "COURSE"
    assert result["operands"][1]["code"] == "CIS*2500"

def test_sprint3_logical_and():
    """
    Tests a simple AND (comma) expression between two courses.
    """
    test_string = "CIS*1910, CIS*2500"
    result = parse_prereq(test_string)[0]

    assert result["type"] == "AND"
    assert len(result["operands"]) == 2
    assert result["operands"][0]["type"] == "COURSE"
    assert result["operands"][1]["code"] == "CIS*2500"

def test_sprint3_operator_precedence_and_first():
    """
    Tests that AND (comma) has higher precedence than OR.
    "A, B OR C" should be parsed as "(A AND B) OR C".
    """
    test_string = "CIS*1910, CIS*2500 OR MATH*1200"
    result = parse_prereq(test_string)[0]

    # Top level should be OR
    assert result["type"] == "OR"
    assert len(result["operands"]) == 2

    # The first operand of the OR should be the AND block
    and_block = result["operands"][0]
    assert and_block["type"] == "AND"
    assert len(and_block["operands"]) == 2
    assert and_block["operands"][0]["code"] == "CIS*1910"
    assert and_block["operands"][1]["code"] == "CIS*2500"

    # The second operand of the OR should be the single course
    course_block = result["operands"][1]
    assert course_block["type"] == "COURSE"
    assert course_block["code"] == "MATH*1200"

def test_sprint3_operator_precedence_or_first():
    """
    Tests the reverse operator precedence.
    "A OR B, C" should be parsed as "A OR (B AND C)".
    """
    test_string = "MATH*1200 OR CIS*1910, CIS*2500"
    result = parse_prereq(test_string)[0]

    # Top level should be OR
    assert result["type"] == "OR"
    assert len(result["operands"]) == 2

    # The first operand of the OR should be the single course
    course_block = result["operands"][0]
    assert course_block["type"] == "COURSE"
    assert course_block["code"] == "MATH*1200"

    # The second operand of the OR should be the AND block
    and_block = result["operands"][1]
    assert and_block["type"] == "AND"
    assert len(and_block["operands"]) == 2
    assert and_block["operands"][0]["code"] == "CIS*1910"
    assert and_block["operands"][1]["code"] == "CIS*2500"

def test_sprint3_longer_and_chain():
    """
    Tests that a chain of ANDs is parsed correctly.
    """
    test_string = "CIS*1910, CIS*2500, CIS*2750"
    result = parse_prereq(test_string)[0]

    assert result["type"] == "AND"
    assert len(result["operands"]) == 3
    assert result["operands"][0]["code"] == "CIS*1910"
    assert result["operands"][1]["code"] == "CIS*2500"
    assert result["operands"][2]["code"] == "CIS*2750"

def test_sprint3_longer_or_chain():
    """
    Tests that a chain of ORs is parsed correctly.
    """
    test_string = "CIS*1910 OR CIS*2500 OR CIS*2750"
    result = parse_prereq(test_string)[0]

    assert result["type"] == "OR"
    assert len(result["operands"]) == 3
    assert result["operands"][0]["code"] == "CIS*1910"
    assert result["operands"][1]["code"] == "CIS*2500"
    assert result["operands"][2]["code"] == "CIS*2750"

    # --- SPRINT 4 TESTS (New) ---

def test_sprint4_simple_grouping():
    """
    Tests a simple grouped expression: A, (B or C)
    This should be parsed as A AND (B OR C).
    """
    test_string = "ECON*3740, (CIS*1300 or CIS*1500)"
    result = parse_prereq(test_string)[0]

    assert result["type"] == "AND"
    assert len(result["operands"]) == 2

    # First operand is the simple course
    assert result["operands"][0]["type"] == "COURSE"
    assert result["operands"][0]["code"] == "ECON*3740"

    # Second operand is the OR block
    or_block = result["operands"][1]
    assert or_block["type"] == "OR"
    assert len(or_block["operands"]) == 2
    assert or_block["operands"][0]["code"] == "CIS*1300"
    assert or_block["operands"][1]["code"] == "CIS*1500"

def test_sprint4_complex_nesting():
    """
    Tests a more complex, multi-level nested expression from the user's examples.
    Structure: (A or B), (C or D), [ (E, F) or G ]
    This should be a top-level AND of three groups.
    """
    test_string = "(AHSS*1210 or MDST*1040), (MDST*1050 or MDST*2080), [(MDST*1100, MDST*1200) or MDST*1080]"
    result = parse_prereq(test_string)[0]

    # Top level is an AND with three operands
    assert result["type"] == "AND"
    assert len(result["operands"]) == 3

    # Check first group: (A or B)
    group1 = result["operands"][0]
    assert group1["type"] == "OR"
    assert group1["operands"][0]["code"] == "AHSS*1210"
    assert group1["operands"][1]["code"] == "MDST*1040"

    # Check second group: (C or D)
    group2 = result["operands"][1]
    assert group2["type"] == "OR"
    assert group2["operands"][0]["code"] == "MDST*1050"
    assert group2["operands"][1]["code"] == "MDST*2080"
    
    # Check third group: [ (E, F) or G ]
    group3 = result["operands"][2]
    assert group3["type"] == "OR"
    
    # The first operand of the third group is another nested group (E, F)
    nested_and_group = group3["operands"][0]
    assert nested_and_group["type"] == "AND"
    assert nested_and_group["operands"][0]["code"] == "MDST*1100"
    assert nested_and_group["operands"][1]["code"] == "MDST*1200"

    # The second operand is a single course G
    assert group3["operands"][1]["code"] == "MDST*1080"

# --- SPRINT 5 TESTS (New) ---

def test_sprint5_simple_unbracketed_nof():
    """
    Tests a simple 'N of' list that isn't enclosed in brackets.
    The comma here must be interpreted as OR.
    """
    test_string = "1 of BIOL*1070, BIOL*1080"
    result = parse_prereq(test_string)[0]

    assert result["type"] == "N_OF"
    assert result["count"] == 1
    assert len(result["operands"]) == 2
    assert result["operands"][0]["type"] == "COURSE"
    assert result["operands"][1]["code"] == "BIOL*1080"

def test_sprint5_course_and_bracketed_nof():
    """
    Tests a top-level AND between a course and a bracketed 'N of' list.
    """
    test_string = "BIOC*2580, [1 of HK*3810, ZOO*3600]"
    result = parse_prereq(test_string)[0]

    assert result["type"] == "AND"
    assert len(result["operands"]) == 2
    
    # First operand is the course
    assert result["operands"][0]["type"] == "COURSE"
    assert result["operands"][0]["code"] == "BIOC*2580"

    # Second operand is the N_OF block
    nof_block = result["operands"][1]
    assert nof_block["type"] == "N_OF"
    assert nof_block["count"] == 1
    assert len(nof_block["operands"]) == 2
    assert nof_block["operands"][0]["code"] == "HK*3810"

def test_sprint5_nof_with_nested_and_group():
    """
    Tests an 'N of' list where one of the choices is a nested AND group.
    Case: [1 of BIOM*3200, (ZOO*3200, ZOO*3210), ZOO*3600]
    """
    test_string = "[1 of BIOM*3200, (ZOO*3200, ZOO*3210), ZOO*3600]"
    result = parse_prereq(test_string)[0]

    assert result["type"] == "N_OF"
    assert result["count"] == 1
    assert len(result["operands"]) == 3

    # Check the first operand (a simple course)
    assert result["operands"][0]["code"] == "BIOM*3200"

    # Check the second operand (the nested AND group)
    nested_and = result["operands"][1]
    assert nested_and["type"] == "AND"
    assert len(nested_and["operands"]) == 2
    assert nested_and["operands"][0]["code"] == "ZOO*3200"
    assert nested_and["operands"][1]["code"] == "ZOO*3210"

    # Check the third operand (a simple course)
    assert result["operands"][2]["code"] == "ZOO*3600"

def test_sprint5_multiple_nofs_and_course():
    """
    Tests a complex top-level AND with multiple 'N of' lists.
    Case: MGMT*3320, [1 of ...], (1 of ...)
    """
    test_string = "MGMT*3320, [1 of ECON*2560, ECON*3560], (1 of FARE*3310, HTM*3120)"
    result = parse_prereq(test_string)[0]

    assert result["type"] == "AND"
    assert len(result["operands"]) == 3

    # Check operand 1 (course)
    assert result["operands"][0]["type"] == "COURSE"
    assert result["operands"][0]["code"] == "MGMT*3320"

    # Check operand 2 (first N_OF)
    nof1 = result["operands"][1]
    assert nof1["type"] == "N_OF"
    assert nof1["count"] == 1
    assert len(nof1["operands"]) == 2

    # Check operand 3 (second N_OF)
    nof2 = result["operands"][2]
    assert nof2["type"] == "N_OF"
    assert nof2["count"] == 1
    assert len(nof2["operands"]) == 2

def test_sprint5_nof_with_mixed_or_separators():
    """
    Tests that the 'or_choice_list' correctly handles both commas and 'OR'.
    """
    test_string = "(2 of CIS*1300, CIS*1500 or CIS*1910)"
    result = parse_prereq(test_string)[0]

    assert result["type"] == "N_OF"
    assert result["count"] == 2
    assert len(result["operands"]) == 3
    assert result["operands"][0]["code"] == "CIS*1300"
    assert result["operands"][1]["code"] == "CIS*1500"
    assert result["operands"][2]["code"] == "CIS*1910"
