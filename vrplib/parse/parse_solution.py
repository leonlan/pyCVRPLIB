from typing import List, TypedDict

from .parse_utils import infer_type, text2lines


class Solution(TypedDict, total=False):
    routes: List[List[int]]
    cost: float


def parse_solution(text: str) -> Solution:
    """
    Parses the text of a solution file formatted in VRPLIB style. A solution
    consists of routes, which are indexed from 1 to n, and possibly other data.

    Parameters
    ----------
    text
        The solution text.

    Returns
    -------
    The soluion data.
    """
    solution: Solution = {"routes": []}

    for line in text2lines(text):
        if "Route" in line:
            route = [int(idx) for idx in line.split(":")[1].split(" ") if idx]
            solution["routes"].append(route)
        elif ":" in line or " " in line:  # Split at first colon or whitespace
            split_at = ":" if ":" in line else " "
            k, v = [word.strip() for word in line.split(split_at, 1)]
            solution[k.lower()] = infer_type(v)  # type: ignore
        else:  # Ignore lines without keyword-value pairs
            continue

    return solution
