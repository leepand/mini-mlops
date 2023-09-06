__all__ = ["validate_semicolon", "validate_balanced_parenthesis", "validate_case_when"]

# Cell
import math
from .utils import *

# Cell
def validate_semicolon(s):
    """Validate query `s` by looking for forgotten semicolon.
    The implication could be the keyword CREATE appearing twice"""
    positions = identify_create_table_view(s)
    validation = {"exit_code": 0, "total_lines": count_lines(s)}
    if len(positions) > 1:
        validation["exit_code"] = 1
        validation["val_lines"] = positions
    return validation


# Cell
def validate_balanced_parenthesis(s):
    """Validate query `s` by looking for
    unbalanced parenthesis
    exit_code:
    * 0 = balanced parenthesis
    * 1 = unbalanced parenthesis, too many (
    * 2 = unbalanced parenthesis, too many )
    """
    positions = []  # container for position of unbalanced parenthesis
    # counter for comments
    k = 0  # 0 = no comment range
    comment_open1 = False  # comment indicator for /* */ comments
    comment_open2 = False  # comment indicator for -- comments
    quote_open1 = False  # quote '
    quote_open2 = False  # quote "
    for i, c in enumerate(s):
        if c == "(" and k == 0:
            positions.append(i)
        elif c == ")" and k == 0:
            if len(positions) == 0:
                return {
                    "exit_code": 1,
                    "val_lines": find_line_number(s, [i]),
                    "total_lines": count_lines(s),
                }
            else:
                positions.pop()
        elif (
            s[i : i + 2] == "/*"
            and not comment_open1
            and not comment_open2
            and not quote_open1
            and not quote_open2
        ):  # if there is an opening comment /*
            k += 1
            comment_open1 = True
        elif (
            s[i : i + 2] == "*/"
            and comment_open1
            and not comment_open2
            and not quote_open1
            and not quote_open2
        ):  # if there is a closing comment */
            k -= 1
            comment_open1 = False
        elif (
            s[i : i + 2] == "--"
            and not comment_open1
            and not comment_open2
            and not quote_open1
            and not quote_open2
        ):  # if there is an opening comment --
            k += 1
            comment_open2 = True
        elif (
            (c == "\n" or s[i : i + 3] == "[c]")
            and not comment_open1
            and comment_open2
            and not quote_open1
            and not quote_open2
        ):  # if the -- comment ends
            k -= 1
            comment_open2 = False
        elif (
            c == "'"
            and not comment_open1
            and not comment_open2
            and not quote_open1
            and not quote_open2
        ):  # if opening quote '
            k += 1
            quote_open1 = True
        elif (
            c == "'"
            and not comment_open1
            and not comment_open2
            and quote_open1
            and not quote_open2
        ):  # if opening quote '
            k -= 1
            quote_open1 = False
        elif (
            c == '"'
            and not comment_open1
            and not comment_open2
            and not quote_open1
            and quote_open2
        ):  # if opening quote '
            k += 1
            quote_open2 = True
        elif (
            c == '"'
            and not comment_open1
            and not comment_open2
            and not quote_open1
            and quote_open2
        ):  # if opening quote '
            k -= 1
            quote_open2 = False
    if len(positions) == 0:
        return {"exit_code": 0, "total_lines": count_lines(s)}
    else:
        return {
            "exit_code": 1,
            "val_lines": find_line_number(s, positions),
            "total_lines": count_lines(s),
        }


# Cell
def validate_case_when(s):
    "Validate query `s` looking for unbalanced case ... end"
    case_pos = identify_in_sql(r"\bcase\b", s)  # positions of case when
    end_pos = identify_in_sql(r"\bend\b", s)  # positions of end keywords
    if len(case_pos) == len(end_pos):
        # build pairs
        case_end = [(case_pos[i], end_pos[i]) for i in range(len(case_pos))]
    else:
        # if not same lenght then right padding
        case_pos_len = len(case_pos)
        end_pos_len = len(end_pos)
        max_case_end = max(case_pos_len, end_pos_len)  # maximal positions
        case_pos = case_pos + [math.inf] * (max_case_end - case_pos_len)
        end_pos = end_pos + [-1] * (max_case_end - end_pos_len)
        case_end = [(case_pos[i], end_pos[i]) for i in range(max_case_end)]
    val_positions = []
    for case, end in case_end:
        # if case is missing, then case = infinity > end
        # if end is missing, then end = -1 < case
        if case > end:
            val_positions.append((case, end))
    validation = {"exit_code": 0, "total_lines": count_lines(s)}
    if len(val_positions) > 0:
        # get line numbers
        val_lines = [
            find_line_number(s, [start])[0]
            if start != math.inf
            else find_line_number(s, [end])[0]
            for start, end in val_positions
        ]
        validation["exit_code"] = 1
        validation["val_lines"] = val_lines
    return validation
