# -*- coding:utf-8 -*-

#  ************************** Copyrights and license ***************************
#
# This file is part of gcovr 8.3+main, a parsing and reporting tool for gcov.
# https://gcovr.com/en/main
#
# _____________________________________________________________________________
#
# Copyright (c) 2013-2025 the gcovr authors
# Copyright (c) 2013 Sandia Corporation.
# Under the terms of Contract DE-AC04-94AL85000 with Sandia Corporation,
# the U.S. Government retains certain rights in this software.
#
# This software is distributed under the 3-clause BSD License.
# For more information, see the README.rst file.
#
# ****************************************************************************

import platform
import logging
import os

import pytest

from gcovr.formats.html.write import _make_short_source_filename

CurrentDrive = os.getcwd()[0:1]


@pytest.mark.parametrize(
    "outfile,source_filename",
    [
        ("../gcovr", "C:\\other_dir\\project\\source.c"),
        ("../gcovr/", "C:\\other_dir\\project\\source.c"),
        ("..\\gcovr", "C:\\other_dir\\project\\source.c"),
        ("..\\gcovr\\", "C:\\other_dir\\project\\source.c"),
        (
            "..\\gcovr",
            "C:\\other_dir\\project\\other_dir\\project\\other_dir\\project\\other_dir\\project\\other_dir\\project\\other_dir\\project\\other_dir\\project\\other_dir\\project\\other_dir\\project\\other_dir\\project\\other_dir\\project\\other_dir\\project\\other_dir\\project\\source.c",
        ),
        ("..\\gcovr\\result.html", "C:\\other_dir\\project\\source.c"),
        (
            "..\\gcovr\\result",
            "C:\\other_dir\\project\\other_dir\\project\\other_dir\\project\\other_dir\\project\\other_dir\\project\\other_dir\\project\\other_dir\\project\\other_dir\\project\\other_dir\\project\\other_dir\\project\\other_dir\\project\\other_dir\\project\\other_dir\\project\\source.c",
        ),
        (
            "C:\\gcovr",
            "C:\\other_dir\\project\\other_dir\\project\\other_dir\\project\\other_dir\\project\\other_dir\\project\\other_dir\\project\\other_dir\\project\\other_dir\\project\\other_dir\\project\\other_dir\\project\\other_dir\\project\\other_dir\\project\\other_dir\\project\\source.c",
        ),
        (
            "C:/gcovr",
            "C:\\other_dir\\project\\other_dir\\project\\other_dir\\project\\other_dir\\project\\other_dir\\project\\other_dir\\project\\other_dir\\project\\other_dir\\project\\other_dir\\project\\other_dir\\project\\other_dir\\project\\other_dir\\project\\other_dir\\project\\source.c",
        ),
        (
            "C:/gcovr_files",
            "C:\\other_dir\\project\\other_dir\\project\\other_dir\\project\\other_dir\\project\\other_dir\\project\\other_dir\\project\\other_dir\\project\\other_dir\\project\\other_dir\\project\\other_dir\\project\\other_dir\\project\\source.c",
        ),
    ],
)
@pytest.mark.skipif(platform.system() != "Windows", reason="only for Windows")
def test_windows_make_short_source_filename(outfile: str, source_filename: str) -> None:
    outfile = outfile.replace("C:", CurrentDrive)
    source_filename = source_filename.replace("C:", CurrentDrive)

    result = _make_short_source_filename(outfile, source_filename)
    logging.info("=" * 100)
    logging.info(outfile)
    logging.info(source_filename)
    logging.info(result)
    assert (
        ":" not in result
        or (  # nosec
            result.startswith(CurrentDrive) and ":" not in result[2:]
        )
    )

    assert len(result) < 256  # nosec
