from pathlib import Path

import numpy as np
from numpy.testing import assert_, assert_equal, assert_raises
from pytest import mark

from vrplib.parse.parse_vrplib import (
    group_specifications_and_sections,
    parse_section,
    parse_specification,
    parse_vrplib,
)

DATA_DIR = Path("tests/data/")


@mark.parametrize(
    "name",
    [
        "C101.txt",  # solomon
        "C1_2_1.txt",  # solomon
        "C101.sol",  # solution
        "NoColonSpecification.txt",
    ],
)
def test_raise_invalid_vrplib_format(name):
    """
    Tests if a RuntimeError is raised when the text is not in VRPLIB format.
    """
    with open(DATA_DIR / name, "r") as fh:
        with assert_raises(RuntimeError):
            parse_vrplib(fh.read())


@mark.parametrize(
    "name",
    [
        "A-n32-k5.vrp",
        "B-n31-k5.vrp",
        "CMT6.vrp",
        "E-n13-k4.vrp",
        "F-n72-k4.vrp",
        "Golden_1.vrp",
        "Li_21.vrp",
        "ORTEC-n242-k12.vrp",
        "P-n16-k8.vrp",
        "X-n101-k25.vrp",
    ],
)
def test_no_raise_valid_vrplib_format(name):
    with open(DATA_DIR / name, "r") as fh:
        parse_vrplib(fh.read())


def test_group_specifications_and_sections():
    """
    Check if instance lines are correctly grouped into specifications
    and sections.
    """
    specs = [
        "NAME : ORTEC-VRPTW-ASYM-00c5356f-d1-n258-k12",
        "COMMENT : ORTEC",
    ]
    sections = [
        "EDGE_WEIGHT_SECTION",
        "0	1908",
        "1994	0",
        "TIME_WINDOW_SECTION",
        "1	0	41340",
        "2	15600	23100",
    ]

    lines = specs + sections + ["EOF"]
    actual_specs, actual_sections = group_specifications_and_sections(lines)

    assert_equal(actual_specs, specs)
    assert_equal(actual_sections, [sections[:3], sections[3:]])


@mark.parametrize(
    "line, key, value",
    [
        ("NAME : Antwerp 1", "name", "Antwerp 1"),  # Whitespace around :
        ("COMMENT:'test' ", "comment", "'test'"),  # No whitespace around :
        ("COMMENT: BKS:1", "comment", "BKS:1"),  # Split at first :
        ("CAPACITY: 30", "capacity", 30),  # int value
        ("CAPACITY: 30.5", "capacity", 30.5),  # float value
        ("name: Antwerp 1", "name", "Antwerp 1"),  # OK if key is not uppercase
    ],
)
def test_parse_specification(line, key, value):
    """
    Tests if a specification line is correctly parsed.
    """
    k, v = parse_specification(line)

    assert_equal(k, key)
    assert_equal(v, value)


@mark.parametrize(
    "lines, desired",
    [
        (
            ["SERVICE_TIME_SECTION", "1  2", "2  3", "3  100"],
            ["service_time", np.array([2, 3, 100])],
        ),
        (
            ["TIME_WINDOW_SECTION", "1  2  3", "2  1  2"],
            ["time_window", np.array([[2, 3], [1, 2]])],
        ),
        (
            ["DEMAND_SECTION", "1  1.1", "2  2.2", "3  3.3"],
            ["demand", np.array([1.1, 2.2, 3.3])],
        ),
        (
            ["DEPOT_SECTION", "1", "2", "3", "-1"],
            ["depot", np.array([0, 1, 2])],
        ),
        (
            # No end token in DEPOT_SECTION
            ["DEPOT_SECTION", "4"],
            ["depot", np.array([3])],
        ),
        (
            ["UNKNOWN_SECTION", "1 1", "1 -1"],
            ["unknown", np.array([1, -1])],
        ),
        (
            ["VEHICLES_ALLOWED_CLIENTS_SECTION", "1 2 3 4", "2 4 5", "3 6"],
            ["vehicles_allowed_clients", [[2, 3, 4], [4, 5], [6]]],
        ),
    ],
)
def test_parse_section(lines, desired):
    """
    Tests if data sections (excluding edge weights) are parsed correctly.
    """
    actual = parse_section(lines, {})

    assert_equal(actual, desired)


def test_parse_vrplib():
    instance = "\n".join(
        [
            "NAME: VRPLIB",
            "EDGE_WEIGHT_TYPE: EXPLICIT",
            "EDGE_WEIGHT_FORMAT: FULL_MATRIX",
            "EDGE_WEIGHT_SECTION",
            "0  1",
            "1  0",
            "SERVICE_TIME_SECTION",
            "1  1",
            "TIME_WINDOW_SECTION",
            "1  1   2",
            "EOF",
        ]
    )
    actual = parse_vrplib(instance)

    desired = {
        "name": "VRPLIB",
        "edge_weight_type": "EXPLICIT",
        "edge_weight_format": "FULL_MATRIX",
        "edge_weight": np.array([[0, 1], [1, 0]]),
        "service_time": np.array([1]),
        "time_window": np.array([[1, 2]]),
    }

    assert_equal(actual, desired)


def test_parse_vrplib_no_explicit_edge_weights():
    """
    Tests if the edge weight section is calculated when the instance does not
    contain an explicit section.
    """
    instance = "\n".join(
        [
            "NAME: VRPLIB",
            "EDGE_WEIGHT_TYPE: FLOOR_2D",
            "NODE_COORD_SECTION",
            "1  0   1",
            "2  1   0",
            "SERVICE_TIME_SECTION",
            "1  1",
            "2  1",
            "TIME_WINDOW_SECTION",
            "1  1   2",
            "2  1   2",
            "EOF",
        ]
    )
    actual = parse_vrplib(instance)

    desired = {
        "name": "VRPLIB",
        "edge_weight_type": "FLOOR_2D",
        "edge_weight": np.array([[0, 1], [1, 0]]),
        "node_coord": np.array([[0, 1], [1, 0]]),
        "service_time": np.array([1, 1]),
        "time_window": np.array([[1, 2], [1, 2]]),
    }

    assert_equal(actual, desired)


def test_parse_vrplib_do_not_compute_edge_weights():
    """
    Tests if the edge weight section is not calculated when the instance does
    not contain an explicit section and the user does not want to compute it.
    """
    instance = "\n".join(
        [
            "NAME: VRPLIB",
            "EDGE_WEIGHT_TYPE: FLOOR_2D",
            "NODE_COORD_SECTION",
            "1  0   1",
            "2  1   0",
            "SERVICE_TIME_SECTION",
            "1  1",
            "2  1",
            "TIME_WINDOW_SECTION",
            "1  1   2",
            "2  1   2",
            "EOF",
        ]
    )
    actual = parse_vrplib(instance, compute_edge_weights=False)
    assert_("edge_weight" not in actual)


def test_parse_vrplib_raises_data_specification_and_section():
    """
    Tests that a ValueError is raised when data is included both as
    specification and section.
    """
    instance = "\n".join(
        [
            "SERVICE_TIME: 10",
            "SERVICE_TIME_SECTION",
            "1    20",
            "2    20",
        ]
    )

    # Service time is both a specification and a section which is not allowed.
    with assert_raises(ValueError):
        parse_vrplib(instance)


def test_parse_vrplib_raises_when_specification_after_section():
    """
    Tests that a ValueError is raised when a specification is presented after
    a data section.
    """
    instance = "\n".join(
        [
            "NODE_COORD_SECTION",
            "1  20  20",
            "NAME: Test",
            "EDGE_WEIGHT_TYPE: EUC_2D",
            "EOF",
        ]
    )

    # Specification after a section is not allowed.
    with assert_raises(ValueError):
        parse_vrplib(instance)


def test_empty_text():
    """
    Tests if an empty text file is still read correctly.
    """
    actual = parse_vrplib("")
    assert_equal(actual, {})
