"""A set of common utilities used within the environments.
These are not intended as API functions, and will not remain stable over time.
"""

color2num = dict(
    gray=30,
    red=31,
    green=32,
    yellow=33,
    blue=34,
    magenta=35,
    cyan=36,
    white=37,
    crimson=38,
)


def colorize(
    string: str, color: str, bold: bool = False, highlight: bool = False
) -> str:
    """Returns string surrounded by appropriate terminal colour codes to print colourised text.
    Args:
        string: The message to colourise
        color: Literal values are gray, red, green, yellow, blue, magenta, cyan, white, crimson
        bold: If to bold the string
        highlight: If to highlight the string
    Returns:
        Colourised string
    """
    attr = []
    num = color2num[color]
    if highlight:
        num += 10
    attr.append(str(num))
    if bold:
        attr.append("1")
    attrs = ";".join(attr)
    return f"\x1b[{attrs}m{string}\x1b[0m"


""" This file contains general utility functionality. """


class BColors:
    """
    Colored command line output formatting
    """

    HEADER = "\033[95m"
    OKBLUE = "\033[94m"
    OKGREEN = "\033[92m"
    WARNING = "\033[93m"
    FAIL = "\033[91m"
    ENDC = "\033[0m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"

    @staticmethod
    def format_colored(string: str, color: str) -> str:
        """Format color of string.
        :param string: the text to print
        :param color: the bash color to use
        :return: the color enriched text
        """
        return color + string + BColors.ENDC

    @staticmethod
    def print_colored(string: str, color: str) -> None:
        """Print color formatted string.
        :param string: the text to print
        :param color: the bash color to use
        """
        print(color + string + BColors.ENDC)


# reward=1.0
# BColors.print_colored(f"-> new overall best model {reward:.5f}!",color=BColors.WARNING)
