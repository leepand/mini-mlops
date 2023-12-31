__all__ = [
    "format_sql_commands",
    "format_sql_file",
    "format_sql_files",
    "format_sql_files_cli",
]

# Cell
import re
import os
import tempfile
import argparse
from glob import glob
from mlopskit.ext import sql_formatter
from .core import *
from .utils import *
from .validation import *

# Cell
def format_sql_commands(s, max_len=82):
    "Format SQL commands in `s`. If SELECT line is longer than `max_len` then reformat line"
    s = s.strip()  # strip file contents
    split_s = split_by_semicolon(s)  # split by query
    # validate semicolon
    validations_semicolon = [validate_semicolon(sp) for sp in split_s]
    val_summary_semicolon = sum([val["exit_code"] for val in validations_semicolon])
    # validate balanced parenthesis
    validations_balanced = [validate_balanced_parenthesis(sp) for sp in split_s]
    val_summary_balanced = sum([val["exit_code"] for val in validations_balanced])
    # validate balanced case when ... end
    val_case_end_balanced = [validate_case_when(sp) for sp in split_s if sp != ""]
    val_summary_case = sum([val["exit_code"] for val in val_case_end_balanced])
    if sum([val_summary_semicolon, val_summary_balanced, val_summary_case]) == 0:
        split_comment_after_semicolon = re.compile("((?:\n|create|select))")
        check_comment_after_semicolon = re.compile(r"[\r\t\f\v ]*(?:\/\*|--)")
        check_ending_semicolon = re.compile(r";\s*$")
        split_s_out = []  # initialize container
        last_i = len(split_s) - 1
        for i, sp in enumerate(split_s):  # split by semicolon
            # take care of comment after semicolon
            # split by first newline and format only the second item
            if check_comment_after_semicolon.match(sp):
                split_s2 = split_comment_after_semicolon.split(sp, maxsplit=1)
            else:
                split_s2 = [sp]
            formatted_split_s2 = [
                "\n\n\n" + format_sql(sp, semicolon=True, max_len=max_len).strip()
                if check_sql_query(sp) and not check_skip_marker(sp)
                else sp
                for sp in split_s2
            ]
            formatted_sp = "".join(formatted_split_s2)
            if i != last_i:
                split_c = split_comment(formatted_sp)
                s_code = "".join([d["string"] for d in split_c if not d["comment"]])
                formatted_sp = (
                    formatted_sp
                    if check_ending_semicolon.search(s_code) or formatted_sp == ""
                    else formatted_sp + ";"
                )
            split_s_out.append("".join(formatted_sp))
        # join by semicolon
        formatted_s = "".join(split_s_out)
        # remove starting and ending newlines
        formatted_s = formatted_s.strip()
        # remove more than 3 newlines
        formatted_s = re.sub(r"\n{4,}", "\n\n\n", formatted_s)
        # add newline at the end of file
        formatted_s = formatted_s + "\n"
        return formatted_s
    else:
        error_dict = {}
        if val_summary_semicolon > 0:
            file_lines = [
                tuple(
                    [
                        line
                        + sum([sd["total_lines"] for sd in validations_semicolon[0:i]])
                        for line in d["val_lines"]
                    ]
                )
                for i, d in enumerate(validations_semicolon)
                if d["exit_code"] == 1
            ]
            error_dict["semicolon"] = {"error_code": 2, "lines": file_lines}
        if val_summary_balanced > 0:
            file_lines = [
                [
                    line + sum([sd["total_lines"] for sd in validations_balanced[0:i]])
                    for line in d["val_lines"]
                ]
                for i, d in enumerate(validations_balanced)
                if d["exit_code"] == 1
            ]
            error_dict["unbalanced_parenthesis"] = {
                "error_code": 3,
                "lines": file_lines,
            }
        if val_summary_case > 0:
            file_lines = [
                [
                    line + sum([sd["total_lines"] for sd in val_case_end_balanced[0:i]])
                    for line in d["val_lines"]
                ]
                for i, d in enumerate(val_case_end_balanced)
                if d["exit_code"] == 1
            ]
            error_dict["unbalanced_case"] = {"error_code": 4, "lines": file_lines}
        return error_dict


# Cell
def format_sql_file(f, max_len=82):
    """Format file `f` with SQL commands and overwrite the file.
    If SELECT line is longer than 82 characters then reformat line
    Return exit_code:
    * 0 = Everything already formatted
    * 1 = Formatting applied
    * 2 = Problem detected, formatting aborted
    """
    # open the file
    with open(f, "r") as file:
        sql_commands = file.read()
    # format SQL statements
    formatted_file = format_sql_commands(sql_commands, max_len=max_len)
    if isinstance(formatted_file, dict):
        print(f"Something went wrong in file: {f}")
        if "semicolon" in formatted_file.keys():
            print(
                (
                    "[WARNING] Identified CREATE keyword more than twice within the same query "
                    + f"at lines {formatted_file['semicolon']['lines']}\n"
                    "You may have forgotten a semicolon (;) to delimit the queries"
                )
            )
        if "unbalanced_parenthesis" in formatted_file.keys():
            print(
                (
                    "[WARNING] Identified unbalanced parenthesis "
                    + f"at lines {formatted_file['unbalanced_parenthesis']['lines']}\n"
                    "You should check your parenthesis"
                )
            )
        if "unbalanced_case" in formatted_file.keys():
            print(
                (
                    "[WARNING] Identified unbalanced case when ... end "
                    + f"at lines {formatted_file['unbalanced_case']['lines']}\n"
                    "You should check for missing case or end keywords"
                )
            )
        print(f"Aborting formatting for file {f}")
        exit_code = 2

        print(f"Aborting formatting for file {f}")
        exit_code = 2

    else:
        exit_code = 0 if sql_commands == formatted_file else 1
        # overwrite file
        with open(f, "w") as f:
            f.write(formatted_file)
    return exit_code


# Cell
def format_sql_files(files, recursive=False, max_len=82):
    "Format SQL `files`"
    exit_codes = []
    # if wildcard "*" is input then use it
    if len(files) == 1 and re.search("\*", files[0]):
        if recursive:  # if recursive search
            files = glob(os.path.join("**", files[0]), recursive=True)
        else:
            files = glob(files[0])
    for file in files:
        exit_codes.append(format_sql_file(file, max_len=max_len))
    if sum(exit_codes) == 0:
        print("Nothing to format, everything is fine!")
    else:
        print("All specified files were formatted!")


# Cell
def format_sql_files_cli():
    "Format SQL files"
    parser = argparse.ArgumentParser(description="Format SQL files")
    parser.add_argument(
        "files",
        help='Path to SQL files. You can also use wildcard using ".*sql"',
        type=str,
        nargs="+",
    )
    parser.add_argument(
        "-r",
        "--recursive",
        help="Should files also be searched in subfolders?",
        action="store_true",
    )
    parser.add_argument(
        "-m",
        "--max-line-length",
        help="Maximum line length for trunction of SELECT fields",
        type=int,
        default=82,
    )
    parser.add_argument(
        "-v",
        "--version",
        action="version",
        version=f"sql_formatter version {sql_formatter.__version__}",
    )
    args = parser.parse_args()
    format_sql_files(
        files=args.files, recursive=args.recursive, max_len=args.max_line_length
    )
