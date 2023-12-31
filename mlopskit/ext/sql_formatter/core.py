__all__ = [
    "MAIN_STATEMENTS",
    "clean_query",
    "preformat_statements",
    "lowercase_query",
    "add_whitespaces_query",
    "format_partition_by",
    "remove_wrong_end_comma",
    "format_case_when",
    "reformat_too_long_line",
    "format_select",
    "format_from",
    "format_join",
    "format_on",
    "format_where",
    "format_statement_line",
    "format_statements",
    "format_multiline_comments",
    "add_semicolon",
    "format_simple_sql",
    "format_sql",
]

# Cell
import re
from .utils import *

# Cell
MAIN_STATEMENTS = [
    "create.*?table",  # regex for all variants, e.g. CREATE OR REPLACE TABLE
    "create.*?view",  # regex for all variants, e.g. CREATE OR REPLACE VIEW
    "select distinct",
    "select",
    "from",
    "left join",
    "inner join",
    "outer join",
    "right join",
    "union",
    "on",
    "where",
    "group by",
    "order by",
    "over",  # special case: no newline, only capitalized
    "partition by",  # special case: no newline, only capitalized
]

# Cell
def clean_query(s):
    "Remove redundant whitespaces, mark comments boundaries and remove newlines afterwards in query `s`"
    s = add_whitespaces_after_comma(
        s
    )  # add whitespaces after comma but no in comments or quotes
    s = remove_redundant_whitespaces(s)  # remove too many whitespaces but no newlines
    s = mark_comments(s)  # mark comments with special tokens [C], [CS] and [CI]
    s = replace_newline_chars(s)  # remove newlines but not in the comments
    s = remove_whitespaces_newline(s)  # remove whitespaces after and before newline
    s = remove_whitespaces_comments(
        s
    )  # remove whitespaces after and before [C], [CS] and [CI]
    s = remove_whitespaces_parenthesis(s)  # remove whitespaces between parenthesis
    s = remove_redundant_whitespaces(s)  # remove too many whitespaces but no newlines
    return s


# Cell
def preformat_statements(s):
    """Write a newline in `s` for all `statements` and
    uppercase them but not if they are inside a comment"""
    statements = MAIN_STATEMENTS
    s = clean_query(s)  # clean query and mark comments
    split_s = split_query(s)  # split by comment and non comment
    split_s = compress_dicts(split_s, ["comment", "select"])
    # compile regex before loop
    create_re = re.compile(r"\bcreate\b", flags=re.I)
    select_re = re.compile(r"\bselect\b", flags=re.I)
    for statement in statements:
        if create_re.match(statement):  # special case CREATE with AS capitalize as well
            create_sub = re.compile(rf"\s*({statement} )(.*) as\b", flags=re.I)
            split_s = [
                {
                    "string": create_sub.sub(
                        lambda pat: "\n" + pat.group(1).upper() + pat.group(2) + " AS",
                        sdict["string"],
                    )
                    if not sdict["comment"]
                    else sdict["string"],
                    "comment": sdict["comment"],
                    "select": sdict["select"],
                }
                for sdict in split_s
            ]
        else:  # normal main statements
            non_select_region_re = re.compile(rf"\s*\b({statement})\b", flags=re.I)
            select_region_statement_re = re.compile(rf"\b({statement})\b", flags=re.I)
            split_s = [
                {
                    "string": non_select_region_re.sub(
                        "\n" + statement.upper(), sdict["string"]
                    )
                    if not sdict["comment"]
                    and not sdict["select"]  # no comment, no select region
                    else non_select_region_re.sub(
                        "\n" + statement.upper(), sdict["string"]
                    )
                    if not sdict["comment"]
                    and sdict["select"]
                    and select_re.match(
                        statement
                    )  # no comment, select region and select statement
                    else select_region_statement_re.sub(
                        statement.upper(), sdict["string"]
                    )
                    if not sdict["comment"]
                    and sdict["select"]
                    and not select_re.match(
                        statement
                    )  # no comment, select region and no select statement
                    else sdict["string"],
                    "comment": sdict["comment"],
                    "select": sdict["select"],
                }
                for sdict in split_s
            ]
    s = "".join([sdict["string"] for sdict in split_s])
    s = s.strip()  # strip string
    s = remove_whitespaces_newline(s)  # remove whitespaces before and after newline
    return s


# Cell
def lowercase_query(s):
    "Lowercase query but let comments and text in quotes untouched"
    split_s = split_query(s)
    split_s = [
        d["string"] if d["comment"] or d["quote"] else d["string"].lower()
        for d in split_s
    ]
    s = "".join([s for s in split_s])
    return s


# Cell
def add_whitespaces_query(s):
    "Add whitespaces between symbols (=!<>) for query `s` but not for comments"
    split_s = split_comment_quote(
        s
    )  # split by comment / non-comment, quote / non-quote
    for d in split_s:
        if not d["comment"] and not d["quote"]:
            d["string"] = add_whitespaces_between_symbols(d["string"])
    s = "".join([d["string"] for d in split_s])
    return s


# Cell
def format_partition_by(s, base_indentation):
    "Format PARTITION BY line in SELECT (DISTINCT)"
    orderby_involved = bool(re.search("order by", s, flags=re.I))
    if orderby_involved:
        split_s = re.split(
            "(partition by.*)(order by.*)", s, flags=re.I
        )  # split PARTITION BY
    else:
        split_s = re.split("(partition by.*)", s, flags=re.I)  # split PARTITION BY
    split_s = [sp for sp in split_s if sp != ""]
    begin_s = split_s[0]
    partition_by = split_s[1]
    indentation = base_indentation + len(begin_s) + 13
    # add newline after each comma (no comments) and indentation
    partition_by = add_newline_indentation(partition_by, indentation=indentation)
    # add new line and indentation after order by
    if orderby_involved:
        partition_by = "".join([partition_by, " "] + split_s[2:])
    partition_by = re.sub(
        r"\s(order by.*)",
        "\n" + " " * (base_indentation + len(begin_s)) + r"\1",
        partition_by,
        flags=re.I,
    )
    # combine begin of string with formatted partition by
    s = begin_s + partition_by
    s = s.strip()
    return s


# Cell
def remove_wrong_end_comma(split_s):
    """Remove mistakenly placed commas at the end of SELECT statement using `split_s` with keys
    "string", "comment" and "quote"
    """
    reversed_split_s = split_s[::-1]  # reversed split_s
    first_noncomment = True
    # compile regex before loop
    replace_comma_without_comment = re.compile(r"([\w\d]+)[,]+(\s*)$")
    replace_comma_with_comment = re.compile(r"([\w\d]+)[,]+(\s*)$")
    for i, d in enumerate(reversed_split_s):
        s_aux = d["string"]
        if (
            not d["comment"]
            and not d["quote"]
            and d["string"] != ""
            and first_noncomment
        ):
            if i == 0:  # if end of select (no comment afterwards) remove whitespaces
                s_aux = replace_comma_without_comment.sub(r"\1", s_aux)
            else:  # if not end of select (because comment afterwards) do not remove whitespaces
                s_aux = replace_comma_with_comment.sub(r"\1\2", s_aux)
            first_noncomment = False
        # remove whitespaces between newline symbols
        s_aux = remove_whitespaces_newline(s_aux)
        reversed_split_s[i]["string"] = s_aux
    split_s_out = reversed_split_s[::-1]
    return split_s_out


# Cell
def format_case_when(s):
    "Format case when statement in line `s`"
    # compile regex
    when_else_re = re.compile(r"(?<!case) ((?:when|else).*?)", flags=re.I)
    case_and_or = re.compile(r"\b((?:and|or))\b", flags=re.I)
    # prepare string
    s_strip = s.strip()
    field_indentation = len(s) - len(s_strip)
    case_when_indentation = identify_in_sql("case when", s_strip)[0]
    split_s = split_comment_quote(s)
    for d in split_s:
        if not d["quote"]:  # assumed no comments given by select function
            d["string"] = when_else_re.sub(  # + 5 = len(case )
                r"\n" + " " * (field_indentation + case_when_indentation + 5) + r"\1",
                d["string"],
            )
            d["string"] = case_and_or.sub(  # + 9 = len(case when )
                r"\1\n" + " " * (field_indentation + case_when_indentation + 9),
                d["string"],
            )
    s_out = "".join([d["string"] for d in split_s])
    return s_out


# Cell
def reformat_too_long_line(li, max_len=82):
    "Reformat too long line `li` if it is longer than `max_len` characters after stripping"
    if len(li.strip()) > max_len:
        function_re = re.compile("[\w\d]+\(")
        if function_re.search(li):
            out_list = []
            in_function = False  # indicator for reformatting line with function
            k = 0  # counter for parenthesis
            j = 0  # indicator for string position
            quote_open1 = False  # quote '
            quote_open2 = False  # quote "
            first_append = True
            for i, s in enumerate(li):
                if (
                    function_re.match(li[i - 1 : i + 1])
                    and not quote_open1
                    and not quote_open2
                    and not in_function
                ):
                    in_function = True
                    indentation = i + 1
                elif s == "(" and not quote_open1 and not quote_open2 and in_function:
                    k += 1
                elif s == ")" and not quote_open1 and not quote_open2 and in_function:
                    k -= 1
                elif k == -1:
                    in_function = False
                elif (
                    s == ","
                    and in_function
                    and not quote_open1
                    and not quote_open2
                    and k == 0
                ):
                    if first_append:
                        out_list.append(li[j : i + 1].rstrip())
                        first_append = False
                    else:
                        out_list.append(li[j : i + 1].strip())
                    j = i + 1
                elif s == "'" and not quote_open1 and not quote_open2:
                    quote_open1 = True
                elif s == "'" and quote_open1 and not quote_open2:
                    quote_open1 = False
                elif s == '"' and not quote_open1 and not quote_open2:
                    quote_open2 = True
                elif s == '"' and not quote_open1 and quote_open2:
                    quote_open2 = False
            out_list.append(li[j:].strip())
            if len(out_list) > 1:
                join_str = "\n" + " " * indentation
                li = join_str.join(out_list)
        elif "in (" in li:
            out_list = []
            in_in = False
            j = 0  # indicator for string position
            quote_open1 = False  # quote '
            quote_open2 = False  # quote "
            first_append = True
            lcol = 0  # line code column
            for i, s in enumerate(li):
                if (
                    "in (" in li[i - 3 : i + 1]
                    and not quote_open1
                    and not quote_open2
                    and not in_in
                ):
                    in_in = True
                    indentation = i + 1
                elif s == ")" and not quote_open1 and not quote_open2 and in_in:
                    in_in = False
                elif s == "," and in_in and not quote_open1 and not quote_open2:
                    line_chunk = li[j : i + 1]
                    lcol = len(line_chunk.strip()) + indentation
                    if first_append:
                        lcol = len(line_chunk.strip())
                        if lcol >= max_len:
                            out_list.append(line_chunk.rstrip())
                            first_append = False
                            j = i + 1
                    else:
                        lcol = len(line_chunk.strip()) + indentation
                        if lcol >= max_len:
                            out_list.append(line_chunk.strip())
                            j = i + 1
                elif s == "'" and not quote_open1 and not quote_open2:
                    quote_open1 = True
                elif s == "'" and quote_open1 and not quote_open2:
                    quote_open1 = False
                elif s == '"' and not quote_open1 and not quote_open2:
                    quote_open2 = True
                elif s == '"' and not quote_open1 and quote_open2:
                    quote_open2 = False
            out_list.append(li[j:].strip())
            if len(out_list) > 1:
                join_str = "\n" + " " * indentation
                li = join_str.join(out_list)
    return li


# Cell
def format_select(s, max_len=82):
    "Format SELECT statement line `s`. If line is longer than `max_len` then reformat line"
    # remove [C] at end of SELECT
    s = re.sub(r"\[C\]$", "", s)
    split_s = split_comment_quote(
        s
    )  # split by comment / non-comment, quote / non-quote
    # if comma is found at the end of select statement then remove comma
    split_s = remove_wrong_end_comma(split_s)
    # check whether there is a SELECT DISTINCT in the code (not comments, not text in quotes)
    s_code = "".join(
        [d["string"] for d in split_s if not d["comment"] and not d["quote"]]
    )
    # save the correct indentation: 16 for select distinct, 7 for only select
    indentation = 16 if re.search("^select distinct", s_code, flags=re.I) else 7
    # get only comment / non-comment
    split_comment = compress_dicts(split_s, ["comment"])
    # add newline after each comma and indentation (this is robust against quotes by construction)
    s = add_newline_indentation(
        "".join([d["string"] for d in split_s if not d["comment"]]),
        indentation=indentation,
    )
    # split by newline
    split_s = s.split("\n")
    # format case when
    split_s = [
        format_case_when(sp) if identify_in_sql("case when", sp) != [] else sp
        for sp in split_s
    ]
    # join by newline
    s = "\n".join(split_s)
    # format PARTITION BY
    begin_s = s[0:indentation]
    split_s = s[indentation:].split("\n" + (" " * indentation))
    partition_by_re = re.compile("partition by", flags=re.I)
    split_s = [
        format_partition_by(line, base_indentation=indentation)
        if partition_by_re.search(line)
        else line
        for line in split_s
    ]
    s = begin_s + ("\n" + (" " * indentation)).join(split_s)
    s = "\n".join([reformat_too_long_line(li, max_len=max_len) for li in s.split("\n")])
    # get comments and preceding string (non-comment)
    comment_dicts = []
    for i, d in enumerate(split_comment):
        if d["comment"]:
            comment_dicts.append(
                {"comment": d["string"], "preceding": split_comment[i - 1]["string"]}
            )
    # assign comments to text
    s = assign_comment(s, comment_dicts)
    return s


# Cell
def format_from(s, **kwargs):
    "Format FROM statement line `s`"
    s = re.sub(r"(from )(.*)", r"\1  \2", s, flags=re.I)  # add indentation
    return s


# Cell
def format_join(s, **kwargs):
    "Format JOIN statement line `s`"
    s = "    " + s  # add indentation
    return s


# Cell
def format_on(s, **kwargs):
    "Format ON statement line `s`"
    s = "        " + s  # add indentation
    split_s = split_comment_quote(s)
    # define regex before loop
    indent_and_or = re.compile(r"\b((?:and|or))\b", flags=re.I)
    for d in split_s:
        if not d["comment"] and not d["quote"]:
            s_aux = d["string"]
            s_aux = indent_and_or.sub(
                r"\1\n" + " " * 10, s_aux
            )  # add newline and indentation for and / or
            d["string"] = s_aux
    # get split comment / non comment
    split_comment = compress_dicts(split_s, ["comment"])
    s_code = "".join([d["string"] for d in split_s if not d["comment"]])
    # strip lines of code from the right
    s_code = "\n".join([sp.rstrip() for sp in s_code.split("\n")])
    # get comments and preceding string (non-comment)
    comment_dicts = []
    for i, d in enumerate(split_comment):
        if d["comment"]:
            comment_dicts.append(
                {"comment": d["string"], "preceding": split_comment[i - 1]["string"]}
            )
    # assign comments to text
    s = assign_comment(s_code, comment_dicts)
    return s


# Cell
def format_where(s, **kwargs):
    "Format WHERE statement line `s`"
    s = re.sub(r"(where )", r"\1 ", s, flags=re.I)  # add indentation afer WHERE
    # split by comment / non comment, quote / non-quote
    split_s = split_comment_quote(s)
    # define regex before loop
    indent_and = re.compile(r"\s*\b(and)\b", flags=re.I)
    indent_or = re.compile(r"\s*\b(or)\b", flags=re.I)
    for d in split_s:
        if not d["comment"] and not d["quote"]:
            s_aux = d["string"]
            s_aux = indent_and.sub(
                "\n" + " " * 3 + r"\1", s_aux
            )  # add newline and indentation for and
            s_aux = indent_or.sub(
                "\n" + " " * 4 + r"\1", s_aux
            )  # add newline and indentation for or
            d["string"] = s_aux
    # get split comment / non comment
    split_comment = compress_dicts(split_s, ["comment"])
    s_code = "".join([d["string"] for d in split_s if not d["comment"]])
    # strip from the right each code line
    s_code = "\n".join([sp.rstrip() for sp in s_code.split("\n")])
    # get comments and preceding string (non-comment)
    comment_dicts = []
    for i, d in enumerate(split_comment):
        if d["comment"]:
            comment_dicts.append(
                {"comment": d["string"], "preceding": split_comment[i - 1]["string"]}
            )
    # assign comments to text
    s = assign_comment(s_code, comment_dicts)
    return s


# Cell
def format_statement_line(s, **kwargs):
    "Format statement line `s`"
    statement_funcs = {
        "select": format_select,
        "from": format_from,
        "left join": format_join,
        "right join": format_join,
        "inner join": format_join,
        "outer join": format_join,
        "on": format_on,
        "where": format_where,
    }
    for key, format_func in statement_funcs.items():
        if re.match(key, s, flags=re.I):
            s = format_func(s, **kwargs)
    return s


# Cell
def format_statements(s, **kwargs):
    "Format statements lines `s`"
    statement_lines = s.split("\n")
    formatted_lines = [
        format_statement_line(line, **kwargs) for line in statement_lines
    ]
    formatted_s = "\n".join(formatted_lines)
    return formatted_s


# Cell
def format_multiline_comments(s):
    "Format multiline comments by replacing multiline comment [CI] by newline and adding indentation"
    split_s = s.split("\n")
    split_out = []
    for sp in split_s:  # loop on query lines
        if re.search(r"\[CI\]", sp):
            indentation = re.search(r"\/\*", sp).start() + 3
            sp_indent = re.sub(r"\[CI\]", "\n" + " " * indentation, sp)
            split_out.append(sp_indent)
        else:
            split_out.append(sp)
    s = "\n".join(split_out)
    return s


# Cell
def add_semicolon(s):
    "Add a semicolon at the of query `s`"
    split_s = s.split("\n")
    last_line = split_s[-1]
    split_c = split_comment(last_line)
    if len(split_c) == 1:
        split_s[-1] = last_line + ";"
    else:
        split_c[0]["string"] = re.sub(
            "(.*[\w\d]+)(\s*)$", r"\1;\2", split_c[0]["string"]
        )
        split_s[-1] = "".join([d["string"] for d in split_c])
    return "\n".join(split_s)


# Cell
def format_simple_sql(s, semicolon=False, max_len=82):
    "Format a simple SQL query without subqueries `s`"
    s = lowercase_query(s)  # everything lowercased but not the comments
    s = preformat_statements(s)  # add breaklines for the main statements
    s = add_whitespaces_query(s)  # add whitespaces between symbols in query
    s = format_statements(s, max_len=max_len)  # format statements
    s = re.sub(r"\[C\]", "", s)  # replace remaining [C]
    s = re.sub(r"\[CS\]", "\n", s)  # replace remaining [CS]
    s = re.sub(r"\s+\n", "\n", s)  # replace redundant whitespaces before newline
    s = format_multiline_comments(s)  # format multline comments
    s = s.strip()  # strip query
    if semicolon:
        s = add_semicolon(s)
    return s


# Cell
def format_sql(s, semicolon=False, max_len=82):
    "Format SQL query with subqueries `s`"
    s = format_simple_sql(
        s, semicolon=semicolon, max_len=max_len
    )  # basic query formatting
    # get first outer subquery positions
    subquery_pos = extract_outer_subquery(s)
    # loop over subqueries
    while subquery_pos is not None:
        # get split
        split_s = [
            s[0 : subquery_pos[0]],
            s[subquery_pos[0] : (subquery_pos[1] + 1)],
            s[(subquery_pos[1] + 1) :],
        ]
        # format subquery (= split_s[1])
        split_s[1] = format_subquery(split_s[1], split_s[0])
        # join main part and subquery
        s = "".join(split_s)
        # get first outer subquery positions
        subquery_pos = extract_outer_subquery(s)
    # remove whitespace between word and parenthesis
    s = re.sub(r"\s*\)", ")", s)
    return s
