# -*- coding:utf-8 -*-

#  ************************** Copyrights and license ***************************
#
# This file is part of gcovr 8.0+main, a parsing and reporting tool for gcov.
# https://gcovr.com/en/main
#
# _____________________________________________________________________________
#
# Copyright (c) 2013-2024 the gcovr authors
# Copyright (c) 2013 Sandia Corporation.
# Under the terms of Contract DE-AC04-94AL85000 with Sandia Corporation,
# the U.S. Government retains certain rights in this software.
#
# This software is distributed under the 3-clause BSD License.
# For more information, see the README.rst file.
#
# ****************************************************************************

# cspell:ignore testopt


import io
import re

import pytest

from gcovr.configuration import (
    GCOVR_CONFIG_OPTIONS,
    GcovrConfigOption,
    merge_options_and_set_defaults,
    parse_config_file,
    parse_config_into_dict,
)


def run_cfg_test(contents, filename="test.cfg"):
    r"""Helper to parse a config file from a string."""

    open_file = io.StringIO(contents)
    return parse_config_file(open_file, filename=filename)


def test_entries_cannot_have_leading_whitespace():
    r"""
    Leading whitespace is forbidden
    in case that will be used for multi-line values,
    similar to MIME headers.
    """

    cfg = "   key = cannot be indented"
    error = 'test.cfg: 1: expected "key = value" entry\n' "on this line: " + cfg
    with pytest.raises(SyntaxError, match=error):
        list(run_cfg_test(cfg))


def test_line_must_have_key_and_value():  # pylint: disable=missing-docstring
    cfg = "must have key and value"
    error = 'test.cfg: 1: expected "key = value" entry\n' "on this line: " + cfg
    with pytest.raises(SyntaxError, match=error):
        list(run_cfg_test(cfg))


@pytest.mark.parametrize(
    "name,cfg",
    [
        ("leading quote", 'key = "value"'),
        ("leading quote", "key = 'value'"),
        ("trailing backslash", "key = value\\\n"),
        ("semicolon comment", "; comment key = value"),
        ("semicolon comment", "key = value ; comment"),
        ("variable substitution", "key = $(var)"),
        ("variable substitution", "key = ${var}"),
        ("variable substitution", "key = $var"),
    ],
)
def test_reserved_config_file_syntax(name, cfg):
    r"""
    Check that some syntax is reserved,
    in case the config file format will be expanded in the future.
    """
    error = re.compile(
        r"test.cfg: 1: {name} .* is reserved".format(name=re.escape(name))
    )
    with pytest.raises(SyntaxError, match=error):
        list(run_cfg_test(cfg))


def test_unknown_keys():
    r"""
    Check that unknown keys always generate an error.

    A key is unknown if:
    -   no such option exists
    -   the config key was explicitly suppressed
    -   a key was autogenerated from the first --long option name,
        but the key refers to the wrong option name.
    """
    all_options = GCOVR_CONFIG_OPTIONS + [
        GcovrConfigOption(
            "testopt",
            ["--testopt"],
            config=False,
            help="for unit tests only",
        ),
        GcovrConfigOption(
            "testopt2",
            ["--testopt2", "--testopt-two"],
            config="testopt2",
            help="for unit tests only",
        ),
    ]

    # completely unknown key
    with pytest.raises(ValueError, match="foo-bar: unknown config option"):
        parse_config_into_dict(run_cfg_test("foo-bar = baz"), all_options=all_options)

    # explicitly suppressed key
    with pytest.raises(ValueError, match="testopt: unknown config option"):
        parse_config_into_dict(run_cfg_test("testopt = value"), all_options=all_options)

    # autogenerated keys only use the first --long flag
    with pytest.raises(ValueError, match="testopt-two: unknown config option"):
        parse_config_into_dict(
            run_cfg_test("testopt-two = value"), all_options=all_options
        )


@pytest.mark.parametrize(
    "test_spec",
    [
        ("type=bool", "testopt-bool", "testopt_bool", True, False, True),
        ("store_true", "delete-gcov-files", "gcov_delete", True, False, True),
        (
            "store_false",
            "html-absolute-paths",
            "html_relative_anchors",
            False,
            True,
            True,
        ),
        ("store_const", "testopt-const", "testopt_const", 17, 3, True),
        ("nargs=?", "testopt-nargs", "testopt_nargs", 49, 11, False),
    ],
    ids=lambda test_spec: test_spec[0],
)
def test_option_with_boolean_values(test_spec):
    r"""
    Boolean values need special consideration.

    In particular, for store_true/store_false/store_const:

    -   if the entry is absent, nothing is assigned.
    -   if the value is "yes", the const value is assigned.
    -   if the value is "no", the default value is explicitly assigned.
    -   if the value is not boolean, an error is raised.

    Boolean options are similar,
    but simply treat yes=True, no=False as their value.
    As far as the config system is concerned,
    there is no difference between store_true and type=bool options.

    Options with nargs='?' are similar,
    but try to parse non-boolean values.
    """

    _, key, target, when_yes, when_no, test_other = test_spec

    all_options = GCOVR_CONFIG_OPTIONS + [
        GcovrConfigOption(
            "testopt_const",
            ["--testopt-const"],
            type=int,
            action="store_const",
            const=17,
            default=3,
            help="for unit tests only",
        ),
        GcovrConfigOption(
            "testopt_bool",
            ["--testopt-bool"],
            type=bool,
            help="for unit tests only",
        ),
        GcovrConfigOption(
            "testopt_nargs",
            ["--testopt-nargs"],
            nargs="?",
            type=int,
            const=49,
            default=11,
            help="for unit tests only",
        ),
    ]

    # the default is not set at this stage
    options = parse_config_into_dict(run_cfg_test(""), all_options=all_options)
    assert "target" not in options

    # if set to "no", nothing the default is explicitly set
    options = parse_config_into_dict(
        run_cfg_test("{key} = no".format(key=key)), all_options=all_options
    )
    assert options[target] == when_no

    # if set to "yes", the value is set
    options = parse_config_into_dict(
        run_cfg_test("{key} = yes".format(key=key)), all_options=all_options
    )
    assert options[target] == when_yes

    if not test_other:
        return

    # if set to an illegal value, an error is raised
    with pytest.raises(ValueError, match="test.cfg: 1: .*: boolean option"):
        parse_config_into_dict(
            run_cfg_test("{key} = garbage".format(key=key)), all_options=all_options
        )


def test_option_choice():
    all_options = GCOVR_CONFIG_OPTIONS + [
        GcovrConfigOption(
            "testopt",
            ["--testopt"],
            type=int,
            choices=(1, 3, 5),
            help="for unit tests only",
        ),
    ]

    # all of these should pass:
    for value in (1, 3, 5):
        options = parse_config_into_dict(
            run_cfg_test("testopt = {value}".format(value=value)),
            all_options=all_options,
        )
        assert options["testopt"] == value

    # all of these should fail:
    for value in (0, 2, 4, 6):
        error = "must be one of (1, 3, 5) but got {}".format(value)
        with pytest.raises(ValueError, match=re.escape(error)):
            parse_config_into_dict(
                run_cfg_test("testopt = {value}".format(value=value)),
                all_options=all_options,
            )


def test_nargs_optional_value():
    all_options = GCOVR_CONFIG_OPTIONS + [
        GcovrConfigOption(
            "testopt",
            ["--testopt"],
            type=int,
            nargs="?",
            const=77,
            default=535417,
            help="for unit tests only",
        ),
    ]

    # boolean cases have already been handled in another test,
    # just verify that the value can also be set.
    options = parse_config_into_dict(
        run_cfg_test("testopt = 3"), all_options=all_options
    )
    assert options["testopt"] == 3


def test_option_that_appends():
    all_options = GCOVR_CONFIG_OPTIONS + [
        GcovrConfigOption(
            "testopt", config="testopt", action="append", help="for unit tests only"
        ),
    ]

    # when absent
    options = parse_config_into_dict(run_cfg_test(""), all_options=all_options)
    assert "testopt" not in options

    # when given once
    options = parse_config_into_dict(
        run_cfg_test("testopt = foo"), all_options=all_options
    )
    assert options["testopt"] == ["foo"]

    # when given thrice
    options = parse_config_into_dict(
        run_cfg_test("testopt = foo\n" "testopt = bar\n" "testopt = qux\n"),
        all_options=all_options,
    )
    assert options["testopt"] == ["foo", "bar", "qux"]


def test_option_validation():
    # when OK
    options = parse_config_into_dict(run_cfg_test("html-medium-threshold = 50%"))
    assert options["html_medium_threshold"] == 50.0

    # when error
    error = "^test.cfg: 1: html-medium-threshold: 123 not in range"
    with pytest.raises(ValueError, match=error):
        parse_config_into_dict(run_cfg_test("html-medium-threshold = 123%"))


class Ref(object):
    r"""
    Container of exactly one element.

    This is useful to represent the presence of a value that may be None.
    """

    def __init__(self, value):
        self.value = value


@pytest.mark.parametrize(
    "test_spec",
    [
        ("both are empty", [None, None], "the default"),
        ("left value", [Ref("from left"), None], "from left"),
        ("right value", [None, Ref("from right")], "from right"),
        ("left and right", [Ref("from left"), Ref("from right")], "from right"),
        ("left value but right None", [Ref("from left"), Ref(None)], None),
    ],
    ids=lambda test_spec: test_spec[0],
)
def test_namespace_merging_overwriting(test_spec):
    _, input_values, result = test_spec

    all_options = GCOVR_CONFIG_OPTIONS + [
        GcovrConfigOption(
            "testopt",
            ["--testopt"],
            default="the default",
            help="for unit tests only",
        ),
    ]

    options = merge_options_and_set_defaults(
        [{"testopt": ref.value} if ref else {} for ref in input_values],
        all_options=all_options,
    )
    assert options.testopt == result


@pytest.mark.parametrize(
    "test_spec",
    [
        ("both are empty", [None, None], None),
        ("value left", [Ref(["from left"]), None], ["from left"]),
        ("value right", [None, Ref(["from right"])], ["from right"]),
        (
            "left and right",
            [Ref(["from left"]), Ref(["from right"])],
            ["from left", "from right"],
        ),
    ],
    ids=lambda test_spec: test_spec[0],
)
def test_namespace_merging_appending(test_spec):
    _, input_values, result = test_spec

    all_options = GCOVR_CONFIG_OPTIONS + [
        GcovrConfigOption(
            "testopt",
            ["--testopt"],
            action="append",
            help="for unit tests only",
        ),
    ]

    options = merge_options_and_set_defaults(
        [{"testopt": ref.value} if ref else {} for ref in input_values],
        all_options=all_options,
    )
    assert options.testopt == result
