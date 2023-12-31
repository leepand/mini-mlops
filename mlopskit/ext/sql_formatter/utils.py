__all__ = [
    "assert_and_print",
    "compress_dicts",
    "remove_whitespaces_newline",
    "remove_whitespaces_comments",
    "remove_redundant_whitespaces",
    "remove_whitespaces_parenthesis",
    "add_whitespaces_between_symbols",
    "mark_ci_comments",
    "mark_comments",
    "split_query",
    "split_apply_concat",
    "split_comment_quote",
    "split_comment",
    "identify_in_sql",
    "split_by_semicolon",
    "replace_newline_chars",
    "sub_in_sql",
    "add_whitespaces_after_comma",
    "identify_end_of_fields",
    "add_newline_indentation",
    "extract_outer_subquery",
    "format_subquery",
    "check_sql_query",
    "check_skip_marker",
    "identify_create_table_view",
    "count_lines",
    "find_line_number",
    "disimilarity",
    "assign_comment",
]

# Cell
import re
from itertools import accumulate
from collections import Counter
import operator

# Cell
def assert_and_print(s_in, s_expected):
    "Assert equality of `s_in` and `s_expected` and print the result of `s_in` if the assertion worked"
    try:
        assert s_in == s_expected
    except:
        print("Assertion failed\n")
        print("Observed:\n")
        print(s_in)
        print("\n")
        print("Expected:\n")
        print(s_expected)
        if isinstance(s_expected, str):
            for i in range(min(len(s_in), len(s_expected))):
                if s_in[i] != s_expected[i]:
                    break
            print(f"Exception found at position {i}:\n")
            print("10-characters window:\n")
            print("Observed:\n")
            print(s_in[max(i - 5, 0) : i + 5])
            print("\n")
            print("Expected:\n")
            print(s_expected[max(i - 5, 0) : i + 5])
        assert s_in == s_expected
    print(s_in)
    return None


# Cell
def compress_dicts(ld, keys):
    "Compress list of dicts `ld` with same `keys` concatenating key 'string'"
    # make sure keys are a list
    keys = (
        [keys] if not isinstance(keys, list) and not isinstance(keys, tuple) else keys
    )
    # make sure we only use the needed keys and not more
    ld = [{k: v for k, v in d.items() if k in set(keys).union(["string"])} for d in ld]
    ld_out = [ld[0]]  # initialize output with reference dict = first element
    for d in ld[1:]:
        # reference comparison items
        ref_cp_items = {k: v for k, v in ld_out[-1].items() if k in keys}
        cp_items = {k: v for k, v in d.items() if k in keys}
        if ref_cp_items == cp_items:
            ld_out[-1]["string"] += d["string"]
        else:
            ld_out.append(d)
    return ld_out


# Cell
def remove_whitespaces_newline(s):
    "Remove whitespaces before and after newline in `s`"
    s = re.sub(r"\n[\r\t\f\v ]+", "\n", s)  # remove whitespaces after newline
    s = re.sub(r"[\r\t\f\v ]+\n", "\n", s)  # remove whitespaces before newline
    return s


# Cell
def remove_whitespaces_comments(s):
    "Remove whitespaces before and after comment tokens in `s`"
    s = re.sub(
        r"\[C\][\r\t\f\v ]+", "[C]", s
    )  # remove whitespaces after comment token [C]
    s = re.sub(
        r"[\r\t\f\v ]+\[C\]", "[C]", s
    )  # remove whitespaces before comment token [C]
    s = re.sub(
        r"\[CS\][\r\t\f\v ]+", "[CS]", s
    )  # remove whitespaces after comment token [CS]
    s = re.sub(
        r"[\r\t\f\v ]+\[CS\]", "[CS]", s
    )  # remove whitespaces before comment token [CS]
    s = re.sub(
        r"\[CI\][\r\t\f\v ]+", "[CI]", s
    )  # remove whitespaces after comment token [CI]
    s = re.sub(
        r"[\r\t\f\v ]+\[CI\]", "[CI]", s
    )  # remove whitespaces before comment token [CI]
    return s


# Cell
def remove_redundant_whitespaces(s):
    "Strip and remove redundant (more than 2) whitespaces in `s` but no newlines in between"
    s = s.strip()
    s = re.sub(
        r"[\r\t\f\v ]{2,}", " ", s
    )  # remove too many whitespaces but not newlines
    return s


# Cell
def remove_whitespaces_parenthesis(s):
    "Remove whitespaces between parenthesis in query `s`"
    s = re.sub(r"\([\r\t\f\v ]+", "(", s)  # remove whitespaces after (
    s = re.sub(r"[\r\t\f\v ]+\)", ")", s)  # remove whitespaces before )
    return s


# Cell
def add_whitespaces_between_symbols(s):
    "Add whitespaces between symbols in line `s`"
    s = re.sub(r"([^\s=!<>])([=!<>]+)", r"\1 \2", s, flags=re.I)  # no space left
    s = re.sub(r"([=!<>]+)([^\s=!<>])", r"\1 \2", s, flags=re.I)  # no space right
    s = re.sub(
        r"([^\s=!<>])([=!<>]+)([^\s=!<>])", r"\1 \2 \3", s, flags=re.I
    )  # no space left and right
    return s


# Cell
def mark_ci_comments(s):
    "Replace new lines in multiline comments by special token [CI]"
    positions = []  # positions of \n in multiline /* */ comments
    # counter for comments
    k = 0  # 0 = no comment range
    comment_open1 = False  # comment indicator for /* */ comments
    comment_open2 = False  # comment indicator for -- comments
    quote_open1 = False  # quote '
    quote_open2 = False  # quote "
    # loop over character positions
    for i, c in enumerate(s):
        if (
            c == "\n"
            and comment_open1
            and not comment_open2
            and not quote_open1
            and not quote_open2
        ):
            positions.append(i)
        elif (
            s[i : i + 2] == "/*"
            and not comment_open1
            and not comment_open2
            and not quote_open1
            and not quote_open2
        ):  # if there is an opening comment /*
            comment_open1 = True
        elif (
            s[i : i + 2] == "*/"
            and comment_open1
            and not comment_open2
            and not quote_open1
            and not quote_open2
        ):  # if there is a closing comment */
            comment_open1 = False
        elif (
            s[i : i + 2] == "--"
            and not comment_open1
            and not comment_open2
            and not quote_open1
            and not quote_open2
        ):  # if there is an opening comment --
            comment_open2 = True
        elif (
            (c == "\n" or s[i : i + 3] == "[c]")
            and not comment_open1
            and comment_open2
            and not quote_open1
            and not quote_open2
        ):  # if the -- comment ends
            comment_open2 = False
        elif (
            c == "'"
            and not comment_open1
            and not comment_open2
            and not quote_open1
            and not quote_open2
        ):  # if opening quote '
            quote_open1 = True
        elif (
            c == "'"
            and not comment_open1
            and not comment_open2
            and quote_open1
            and not quote_open2
        ):  # if opening quote '
            quote_open1 = False
        elif (
            c == '"'
            and not comment_open1
            and not comment_open2
            and not quote_open1
            and quote_open2
        ):  # if opening quote '
            quote_open2 = True
        elif (
            c == '"'
            and not comment_open1
            and not comment_open2
            and not quote_open1
            and quote_open2
        ):  # if opening quote '
            quote_open2 = False
    if len(positions) == 0:
        return s
    else:
        s = "".join([c if i not in positions else "[CI]" for i, c in enumerate(s)])
        return s


# Cell
def mark_comments(s):
    "Mark end of comments -- and begin of comments /* */ if they are in a new line with token [C]"
    s = re.sub(r"(--.*?)(\n)", r"\1[C]\2", s)  # mark end of -- comments
    s = re.sub(
        r"(\/\*.*?\*\/)", r"\1[C]", s, flags=re.DOTALL
    )  # mark end of /* */ comments
    s = re.sub(
        r"(\n)\s*(--.*?)", r"\1[CS]\2", s, flags=re.DOTALL
    )  # mark start of comment line with --
    s = re.sub(
        r"(\n)\s*(\/\*.*\*\/)", r"\1[CS]\2", s
    )  # mark start of comment line with /*
    s = re.sub(
        r"(\n)\s*(\/\*.*?\*\/)", r"\1[CS]\2", s, flags=re.DOTALL
    )  # mark start of comment line with /*
    s = mark_ci_comments(s)  # replace intercomment new lines by [CI]
    return s


# Cell
def split_query(s):
    """Split query into comment / non-comment, quote / non-quote, select / non-select
    Return a dict with keys "string", "comment" in (True, False) "quote" in (True, False)
    and "select" in (True, False)
    """
    s_low = s.lower()  # lowercased string
    k = 0  #     # counter for comments; 0 = no comment
    comment_open1 = False  # comment indicator for /* */ comments
    comment_open2 = False  # comment indicator for -- comments
    quote_open1 = False  # quote '
    quote_open2 = False  # quote "
    select_region = False  # start with non-select
    quote_region = False  # start with non-quote
    comment_region = False  # start with non-quote
    s_comp = []  # container for string components
    start = 0
    select_re = re.compile(r"^[\n\s\]\(]*\bselect\b\s$")
    from_re = re.compile(r"^[\n\s\]]\bfrom\b\s$")
    # loop over character positions
    for i, c in enumerate(s):
        if (
            select_re.match(s_low[max(i - 1, 0) : i + 7]) and k == 0
        ):  # k = 0 -> no comment
            s_comp.append(
                {
                    "string": s[start:i],
                    "comment": comment_region,
                    "quote": quote_region,
                    "select": select_region,
                }
            )
            start = i
            select_region = True  # after select starts the select region
        elif from_re.match(s_low[max(i - 1, 0) : i + 5]) and k == 0:
            select_open = False
            s_comp.append(
                {
                    "string": s[start:i],
                    "comment": comment_region,
                    "quote": quote_region,
                    "select": select_region,
                }
            )
            start = i
            select_region = False  # after from ends the select region
        elif (
            s[i : i + 4] == "[CS]"
            and not comment_open1
            and not comment_open2
            and not quote_open1
            and not quote_open2
        ):  # if there is an opening full line comment
            k += 1
            s_comp.append(
                {
                    "string": s[start:i],
                    "comment": comment_region,
                    "quote": quote_region,
                    "select": select_region,
                }
            )
            start = i
            comment_region = True
            if s[i : i + 6] == "[CS]/*":
                comment_open1 = True
            else:
                comment_open2 = True
        elif (
            s[i : i + 2] == "/*"
            and not comment_open1
            and not comment_open2
            and not quote_open1
            and not quote_open2
        ):  # if there is an opening comment /*
            k += 1
            # before opening comment it was no comment
            s_comp.append(
                {
                    "string": s[start:i],
                    "comment": comment_region,
                    "quote": quote_region,
                    "select": select_region,
                }
            )
            start = i
            comment_open1 = True
            comment_region = True
        elif (
            s[i : i + 5] == "*/[C]"
            and comment_open1
            and not comment_open2
            and not quote_open1
            and not quote_open2
        ):  # if there is a closing comment */
            k -= 1
            s_comp.append(
                {
                    "string": s[start : i + 5],
                    "comment": comment_region,
                    "quote": quote_region,
                    "select": select_region,
                }
            )  # before closing comment it was comment
            comment_open1 = False
            comment_region = False
            start = i + 5
        elif (
            s[i : i + 2] == "*/"
            and comment_open1
            and not comment_open2
            and not quote_open1
            and not quote_open2
        ):  # if there is a closing comment */
            k -= 1
            s_comp.append(
                {
                    "string": s[start : i + 2],
                    "comment": comment_region,
                    "quote": quote_region,
                    "select": select_region,
                }
            )  # before closing comment it was comment
            comment_open1 = False
            comment_region = False
            start = i + 2
        elif (
            s[i : i + 2] == "--"
            and not comment_open1
            and not comment_open2
            and not quote_open1
            and not quote_open2
        ):  # if there is an opening comment --
            k += 1
            s_comp.append(
                {
                    "string": s[start:i],
                    "comment": comment_region,
                    "quote": quote_region,
                    "select": select_region,
                }
            )  # before opening comment it was no comment
            comment_open2 = True
            comment_region = True
            start = i
        elif (
            (c == "\n" or s[i : i + 3] == "[C]")
            and not comment_open1
            and comment_open2
            and not quote_open1
            and not quote_open2
        ):  # if the -- comment ends
            k -= 1
            comment_open2 = False
            if c == "\n":
                s_comp.append(
                    {
                        "string": s[start:i],
                        "comment": comment_region,
                        "quote": quote_region,
                        "select": select_region,
                    }
                )  # before closing comment it was comment
                start = i
            else:  # [C]
                s_comp.append(
                    {
                        "string": s[start : i + 3],
                        "comment": comment_region,
                        "quote": quote_region,
                        "select": select_region,
                    }
                )  # before closing comment it was comment
                start = i + 3
            comment_region = False
        elif (
            c == "'"
            and not comment_open1
            and not comment_open2
            and not quote_open1
            and not quote_open2
        ):
            s_comp.append(
                {
                    "string": s[start : i + 1],
                    "comment": comment_region,
                    "quote": quote_region,
                    "select": select_region,
                }
            )  # before opening comment it was no comment
            quote_open1 = True
            quote_region = True
            start = i + 1
        elif (
            c == "'"
            and not comment_open1
            and not comment_open2
            and quote_open1
            and not quote_open2
        ):
            s_comp.append(
                {
                    "string": s[start:i],
                    "comment": comment_region,
                    "quote": quote_region,
                    "select": select_region,
                }
            )  # before opening comment it was no comment
            quote_open1 = False
            quote_region = False
            start = i
        elif (
            c == '"'
            and not comment_open1
            and not comment_open2
            and not quote_open1
            and not quote_open2
        ):
            s_comp.append(
                {
                    "string": s[start : i + 1],
                    "comment": comment_region,
                    "quote": quote_region,
                    "select": select_region,
                }
            )  # before opening comment it was no comment
            quote_open2 = True
            quote_region = True
            start = i + 1
        elif (
            c == '"'
            and not comment_open1
            and not comment_open2
            and not quote_open1
            and quote_open2
        ):
            s_comp.append(
                {
                    "string": s[start:i],
                    "comment": comment_region,
                    "quote": quote_region,
                    "select": select_region,
                }
            )  # before opening comment it was no comment
            quote_open2 = False
            quote_region = False
            start = i
    s_comp.append(
        {
            "string": s[start:],
            "comment": comment_region,
            "quote": quote_region,
            "select": select_region,
        }
    )
    s_comp = [d for d in s_comp if d["string"] != ""]  # remove empty strings
    return s_comp


# Cell
def split_apply_concat(s, f):
    "Split query `s`, apply function `f` and concatenate strings"
    return "".join([d["string"] for d in f(split_query(s))])


# Cell
def split_comment_quote(s):
    "Split query `s` into dictionaries with keys 'string', 'comment' and 'quote'"
    split_s = split_query(s)
    # compress all strings with same keys
    split_s = compress_dicts(split_s, keys=["comment", "quote"])
    return split_s


# Cell
def split_comment(s):
    "Split query `s` into dictionaries with keys 'string', 'comment'"
    split_s = split_query(s)
    # compress all strings with same keys
    split_s = compress_dicts(split_s, keys=["comment"])
    return split_s


# Cell
def identify_in_sql(regex, s):
    "Find positions of `regex` (str or list) in string `s` ignoring comment and text in quotes"
    split_s = split_comment_quote(
        s
    )  # split by comment / non-comment and quote / non-quote
    regex = (
        [regex] if not isinstance(regex, list) else regex
    )  # put keyword into list if it is a string
    positions = []  # define output container
    cumul_len = 0  # cumulative length of string
    for d in split_s:  # loop on dictionaries with strings
        if (
            not d["comment"] and not d["quote"]
        ):  # only for non comments and non text in quotes
            for reg in regex:  # loop on regex
                aux_positions = [
                    match.start() for match in re.finditer(reg, d["string"], flags=re.I)
                ]
                if len(aux_positions) > 0:  # if found some matches
                    # add the cumulative length of the string for the actual position in the whole string
                    aux_positions = [pos + cumul_len for pos in aux_positions]
                    positions.extend(aux_positions)
        # increase the cumulative length
        cumul_len += len(d["string"])
    positions = sorted(positions)  # sort positions before returning
    return positions


# Cell
def split_by_semicolon(s):
    "Split string `s` by semicolon but not between parenthesis or in comments"
    positions = identify_in_sql(";", s)  # get semicolon positions
    if positions is []:  # if no semicolon then return full string
        return s
    # add the 0 position if there is no one
    positions = [0] + positions if 0 not in positions else positions
    # loop on start-end of string pairs
    split_s = []  # initialize output
    for start, end in zip(positions, positions[1:] + [None]):
        # return splits
        if start == 0:
            split_s.append(s[start:end])
        else:
            split_s.append(s[start + 1 : end])  # do not take the semicolon
    return split_s


# Cell
def replace_newline_chars(s):
    "Replace newline characters in `s` by whitespace but not in the comments"
    positions = identify_in_sql("\n", s)
    clean_s = "".join([c if i not in positions else " " for i, c in enumerate(s)])
    return clean_s


# Cell
def sub_in_sql(regex, repl, s):
    "Subsitute `regex` with `repl` in query `s` ignoring comments and text in quotes"
    split_s = split_comment_quote(
        s
    )  # split by comment / non-comment and quote / non-quote
    for d in split_s:  # loop on dictionaries with strings
        if (
            not d["comment"] and not d["quote"]
        ):  # only for non comments and non text in quotes
            d["string"] = re.sub(regex, repl, d["string"])
    s = "".join(d["string"] for d in split_s)
    return s


# Cell
def add_whitespaces_after_comma(s):
    "Add whitespace after comma in query `s` if there is no whitespace"
    s = sub_in_sql(r",([\w\d]+)", r", \1", s)
    return s


# Cell
def identify_end_of_fields(s):
    "Identify end of fields in query `s`"
    # container for positions
    end_of_fields = []
    # counter for parenthesis and comments
    k = 0
    quote_open1 = False
    quote_open2 = False
    # loop over string characters
    for i, c in enumerate(s):
        if (
            c == "," and k == 0 and not quote_open1 and not quote_open2
        ):  # field without parenthesis or after closing parenthesis
            after_c = s[i : i + 6]
            if not bool(re.search(r"(?:--|\/\*|\[C\]|\[CS\])", after_c)):
                end_of_fields.append(i)
        elif (
            (c == "(" or s[i : i + 2] in ("--", "/*"))
            and not quote_open1
            and not quote_open2
        ):  # if there is an opening parenthesis or comment
            k += 1
        elif (
            (c == ")" or s[i : i + 3] == "[C]") and not quote_open1 and not quote_open2
        ):  # if there is a closing parenthesis or closing comment
            k -= 1
        elif c == "'" and not quote_open1 and not quote_open2:
            quote_open1 = True
        elif c == "'" and quote_open1 and not quote_open2:
            quote_open1 = False
        elif c == '"' and not quote_open1 and not quote_open2:
            quote_open2 = True
        elif c == '"' and not quote_open1 and quote_open2:
            quote_open2 = False
    return end_of_fields


# Cell
def add_newline_indentation(s, indentation):
    "Add newline and indentation for end of fields in query `s`"
    split_s = []
    positions = identify_end_of_fields(s)
    if positions is []:
        return s
    else:  # add the first position 0
        # add + 1 for the end position
        positions = [0] + [pos + 1 for pos in positions]
    for start, end in zip(positions, positions[1:] + [None]):
        # strip from the left to remove whitespaces
        split_s.append(s[start:end].lstrip())  # get string part
        split_s.append("\n" + " " * indentation)  # add indentation
    s = "".join(split_s)
    s = s.strip()
    return s


# Cell
def extract_outer_subquery(s):
    "Extract outer subquery in query `s`"
    # initialize container for subquery positions
    # in string `s`
    subquery_pos = []
    # auxiliar indicator to get the subquery right
    ind = True
    # counter for parenthesis
    k = 0
    # loop over string characters
    for i, c in enumerate(s):
        if s[i : (i + 8)] == "(\nSELECT" and ind:  # query start
            subquery_pos.append(i)
            k = 0  # set the parenthesis counter to 0
            # turn off the indicator for the program to know
            # that we already hit the subquery start
            ind = False
        elif c == "(":  # if there is a parenthesis not involving a subquery
            k += 1
        elif c == ")" and k == 0 and not ind:  # end position for subquery
            subquery_pos.append(i)
            return subquery_pos
        elif c == ")":
            k -= 1


# Cell
def format_subquery(s, previous_s):
    "Format subquery in line `s` based on indentation on `previous_s`"
    s = re.sub(
        r"^\(\nSELECT", "(SELECT", s
    )  # remove newline between parenthesis and SELECT
    # get reference line for the indentation level
    # and remove whitespaces from the left
    last_line = previous_s.split("\n")[-1]
    ref_line = last_line.lstrip()
    # if the line contains a JOIN statement then indent with
    # 4 whitespaces
    if re.match(r"\w+ join", ref_line, flags=re.I):
        ref_line = "    " + ref_line
    indentation = len(ref_line) + 1  # get indentation level
    split_s = s.split("\n")  # get lines in subquery
    indented_s = [
        " " * indentation + line  # indent all lines the same
        if not re.match(r"SELECT", line)
        else line
        for line in split_s[1:]
    ]
    # SELECT line + indented lines afterwards
    formatted_split = [split_s[0]] + indented_s
    # concatenate with newline character
    formatted_s = "\n".join(formatted_split)
    return formatted_s


# Cell
def check_sql_query(s):
    """Checks whether `s` is a SQL query based on match of CREATE TABLE / VIEW or SELECT ignoring comments and text
    in quotes"""
    split_s = split_query(
        s
    )  # split in comment / non-comment, quote / non-quote regions
    s_code = "".join(
        [d["string"] for d in split_s if not d["comment"] and not d["quote"]]
    )
    return bool(
        re.search(
            pattern=r".*(?:select|create.{0,10}(?:table|view)).*",
            string=s_code,
            flags=re.I,
        )
    ) and not bool(
        re.search(pattern=r"create(?!.*(?:table|view))", string=s_code, flags=re.I)
    )


# Cell
def check_skip_marker(s):
    "Checks whether user set marker /*skip-formatter*/ to not format query"
    return bool(re.search(r"\/\*skip-formatter\*\/", s))


# Cell
def identify_create_table_view(s):
    "Identify positions of CREATE .. TABLE / VIEW statements"
    split_s = split_query(s)
    s_without_comments = "".join([sd["string"] for sd in split_s if not sd["comment"]])
    s_lines = s_without_comments.split("\n")
    line_numbers = [
        i + 1
        for i, line in enumerate(s_lines)
        if re.search("(?:create.*?table|create.*?view)", line, flags=re.I)
    ]
    return line_numbers


# Cell
def count_lines(s):
    "Count the number of lines in `s`"
    return s.count("\n")


# Cell
def find_line_number(s, positions):
    "Find line number in `s` out of `positions`"
    return [s[0:pos].count("\n") + 1 for pos in positions]


# Cell
def disimilarity(str1, str2):
    "Calculate disimilarity between two strings by word"
    # split by space or comma
    split1 = re.split(r"(?:\s|,)", str1)
    split1 = [sp for sp in split1 if sp != ""]
    split2 = re.split(r"(?:\s|,)", str2)
    split2 = [sp for sp in split2 if sp != ""]
    count1 = Counter(split1)
    count2 = Counter(split2)
    all_words = set(list(count1.keys()) + list(count2.keys()))
    disimilarity = 0
    for w in all_words:
        disimilarity += abs(count1[w] - count2[w])
    return disimilarity


# Cell
def assign_comment(fs, cds):
    """Assign comments in list of dictionaries `cds` to formatted string `fs` using Jaccard distance
    The comment dictionaries `cds` should contain the keys "comment" and "preceding" (string)
    """
    fsplit_s = fs.split("\n")
    number_of_lines = len(fsplit_s)
    # define container for output
    fsplit_s_out = fsplit_s.copy()
    # compile regex before loop
    replace_and_or = re.compile(r"\b(?:and|or)\b", flags=re.I)
    replace_c = re.compile(r"\[C\]")
    match_beginn_cs = re.compile(r"^\[CS\]")
    replace_select = re.compile(r"\b(?:select distinct |select )", flags=re.I)
    # loop on comments to be assigned
    for i, d in enumerate(cds):
        cum_preceding = "".join([d["preceding"] for d in cds[0 : i + 1]])
        cp_list = [
            disimilarity(replace_and_or.sub("", s.strip()), cum_preceding)
            for s in accumulate([s for s in fsplit_s], operator.add)
        ]
        # get line number with maximal jaccard distance (most similar)
        line_number = min(enumerate(cp_list), key=lambda x: x[1])[0]
        line = fsplit_s[line_number]
        next_line = (
            fsplit_s[
                line_number + 1
            ]  # next line is relevant for indentation of whole line comments
            if line_number < number_of_lines - 1
            else fsplit_s[
                line_number
            ]  # if there is no next line then take the current line
        )
        indentation = len(next_line) - len(replace_select.sub("", next_line.lstrip()))
        # add comment to it and replace [C] by empty string and [CS] by newline + proper indentation
        whitespace = "" if match_beginn_cs.match(d["comment"]) else " "
        fsplit_s_out[line_number] += whitespace + re.sub(
            "\[CS\]", "\n" + " " * indentation, replace_c.sub("", d["comment"])
        )
    s_out = "\n".join(fsplit_s_out)
    return s_out
