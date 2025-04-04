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

# cspell:ignore ncloc coveredelements coveredconditionals coveredstatements coveredmethods

from dataclasses import dataclass
import logging
from lxml import etree  # nosec # We only write XML files

from ...data_model.container import CoverageContainer
from ...data_model.coverage import LineCoverage
from ...options import Options
from ...utils import get_md5_hexdigest, write_xml_output

LOGGER = logging.getLogger("gcovr")


def write_report(
    covdata: CoverageContainer, output_file: str, options: Options
) -> None:
    """produce an XML report in the Cobertura format"""

    timestamp = str(int(options.timestamp.timestamp()))

    root_elem = etree.Element("coverage")
    root_elem.set("clover", timestamp)
    root_elem.set("generated", timestamp)

    project_elem = etree.SubElement(root_elem, "project")
    if options.clover_project:
        project_elem.set("name", options.clover_project)
    project_elem.set("timestamp", timestamp)
    project_metrics = _metrics_element()
    project_elem.append(project_metrics)
    project_data = ProjectData(0, 0, 0, 0)

    # Generate the coverage output (on a per-package basis)
    packages = dict[str, PackageData]()

    for _, filecov in sorted(covdata.items()):
        filename = filecov.presentable_filename(options.root_filter)
        if "/" in filename:
            directory, fname = filename.rsplit("/", 1)
        else:
            directory, fname = "root", filename

        package_data = packages.setdefault(
            directory,
            PackageData({}, 0, 0, 0),
        )
        file_elem = etree.Element("file")
        file_metrics = _metrics_element()
        file_elem.append(file_metrics)
        class_elem = etree.SubElement(file_elem, "class")
        class_elem.set("name", f"id${get_md5_hexdigest(filename.encode())}")
        class_metrics = _metrics_element()
        class_elem.append(class_metrics)

        loc = 0
        ncloc = 0
        covered_elements = 0
        for linecov in filecov.lines.values():
            loc = linecov.lineno
            if linecov.is_reportable:
                ncloc += 1
                if linecov.is_covered:
                    covered_elements += 1
                file_elem.append(_line_element(linecov))

        file_elem.set("name", fname)
        file_elem.set("path", filename)

        file_metrics.set("classes", "1")
        file_metrics.set("loc", str(loc))
        file_metrics.set("ncloc", str(ncloc))
        file_metrics.set("elements", str(ncloc))
        file_metrics.set("coveredelements", str(covered_elements))

        class_metrics.set("elements", str(ncloc))
        class_metrics.set("coveredelements", str(covered_elements))

        package_data.files_xml[fname] = file_elem
        package_data.loc += loc
        package_data.ncloc += ncloc
        package_data.covered_elements += covered_elements

        project_data.files += 1
        project_data.loc += loc
        project_data.ncloc += ncloc
        project_data.covered_elements += covered_elements

    project_metrics.set("packages", str(len(packages)))
    project_metrics.set("classes", str(project_data.files))
    project_metrics.set("files", str(project_data.files))
    project_metrics.set("loc", str(project_data.loc))
    project_metrics.set("ncloc", str(project_data.ncloc))
    project_metrics.set("elements", str(project_data.ncloc))
    project_metrics.set("coveredelements", str(project_data.covered_elements))

    for package_name in sorted(packages):
        package_data = packages[package_name]
        package_elem = etree.SubElement(project_elem, "package")
        package_metrics = _metrics_element()
        package_elem.append(package_metrics)
        number_files = str(len(package_data.files_xml))
        package_metrics.set("classes", number_files)
        package_metrics.set("files", number_files)
        package_metrics.set("loc", str(package_data.loc))
        package_metrics.set("ncloc", str(package_data.ncloc))
        package_metrics.set("elements", str(package_data.ncloc))
        package_metrics.set("coveredelements", str(package_data.covered_elements))
        for fname in sorted(package_data.files_xml):
            package_elem.append(package_data.files_xml[fname])
        package_elem.set("name", package_name.replace("/", "."))

    # WTH is this needed???
    testproject_elem = etree.SubElement(root_elem, "testproject")
    testproject_elem.set("timestamp", timestamp)
    testproject_metrics = _metrics_element()
    testproject_elem.append(testproject_metrics)
    package_elem = etree.SubElement(testproject_elem, "package")
    package_elem.set("name", "dummy")
    package_metrics = _metrics_element()
    package_elem.append(package_metrics)
    file_elem = etree.Element("file")
    file_elem.set("name", "dummy")
    file_elem.set("path", "dummy")
    package_elem.append(file_elem)
    file_metrics = _metrics_element()
    file_elem.append(file_metrics)
    class_elem = etree.SubElement(file_elem, "class")
    class_elem.set("name", f"id${get_md5_hexdigest(b'dummy')}")
    class_metrics = _metrics_element()
    class_elem.append(class_metrics)

    write_xml_output(
        root_elem,
        pretty=options.clover_pretty,
        filename=output_file,
        default_filename="clover.xml",
        # doctype="<!DOCTYPE coverage SYSTEM 'https://bitbucket.org/atlassian/clover/raw/a688248db8ae15eb7158947b7ba275c9ffbaf008/etc/schema/clover.xsd'>",
    )


@dataclass
class ProjectData:
    """Data class for the project data."""

    files: int
    loc: int
    ncloc: int
    covered_elements: int


@dataclass
class PackageData:
    """Data class for the package data."""

    files_xml: dict[str, etree._Element]
    loc: int
    ncloc: int
    covered_elements: int


def _metrics_element() -> etree._Element:
    elem = etree.Element("metrics")
    for metric in [
        "complexity",
        "elements",
        "coveredelements",
        "conditionals",
        "coveredconditionals",
        "statements",
        "coveredstatements",
        "coveredmethods",
        "methods",
    ]:
        elem.set(metric, "0")

    return elem


def _line_element(line: LineCoverage) -> etree._Element:
    elem = etree.Element("line")
    elem.set("num", str(line.lineno))
    elem.set("type", "stmt")
    elem.set("count", str(line.count))

    return elem
