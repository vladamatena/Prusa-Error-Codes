# This file is part of the SL1 firmware
# Copyright (C) 2020 Prusa Research a.s. - www.prusa3d.com
# SPDX-License-Identifier: GPL-3.0-or-later

"""
Base classes for SL1 errors and warnings
"""

import functools
import json
from enum import unique, IntEnum
from typing import Optional, TextIO, Dict


@unique
class Class(IntEnum):
    """
    Prusa error category codes

    This mapping is taken from general Prusa guidelines on errors, do not modify.
    """
    MECHANICAL = 1  # Mechanical failures, engines XYZ, tower
    TEMPERATURE = 2  # Temperature measurement, thermistors, heating
    ELECTRICAL = 3  # Electrical, MINDA, FINDA, Motion Controller, …
    CONNECTIVITY = 4  # Connectivity - Wi - Fi, LAN, Prusa Connect Cloud
    SYSTEM = 5  # System - BSOD, ...


@functools.total_ordering
class Code:
    """
    Code class holds error code information
    """
    def __init__(self, cls: Class, code: int, message: Optional[str]):
        if cls.value < 0 or cls.value > 9:
            raise ValueError(f"Error class {cls.value} out of range")

        if code < 0 or code > 99:
            raise ValueError(f"Error code {code} out of range")

        self._category = cls
        self._code = code
        self._message = message

    @property
    def code(self) -> int:
        """
        Get error code value

        :return: Error code value
        """
        return self._category.value * 100 + self._code

    @property
    def category(self) -> Class:
        """
        Ger error category

        :return: Error category enum instance
        """
        return self._category

    @property
    def message(self) -> str:
        """
        Get error message

        :return: Error message string
        """
        return self._message

    def __lt__(self, other):
        if not isinstance(other, Code):
            return NotImplemented
        return self.code < other.code

    def __eq__(self, other):
        if not isinstance(other, Code):
            return NotImplemented
        return self.code == other.code

    def __repr__(self):
        return f"Code: Category: {self.category} Value: {self._code} Code: {self.code} Message: {self.message}"

    def __str__(self):
        return f"Code: {self.code} ({self.message})"

    def __int__(self):
        return self.code


class Codes:
    """
    Base class for code listing classes
    """
    @classmethod
    def get_codes(cls) -> Dict[str, Code]:
        """
        Get dictionary containing member codes

        :return: Member code dict
        """
        return {item: var for item, var in vars(cls).items() if isinstance(var, Code)}

    @classmethod
    def dump_json(cls, file: TextIO) -> None:
        """
        Dump codes JSON representation to an open file

        :param file: Where to dump
        :return: None
        """
        obj = {name.lower(): {"code": code.code, "message": code.message} for name, code in cls.get_codes().items()}
        return json.dump(obj, file, indent=True)

    @classmethod
    def dump_cpp_enum(cls, file: TextIO) -> None:
        """
        Dump codes C++ enum representation to an open file

        :param file: Where to dump
        :return: None
        """
        file.write("// Generated error code enum\n")
        file.write("enum class Errors {\n")

        for name, code in cls.get_codes().items():
            file.write(f"\t{name} = {code.code};\n")

        file.write("};\n")

    @classmethod
    def dump_cpp_messages(cls, file: TextIO) -> None:
        """
        Dump code messages C++ QMap representation to an open file

        :param file: Where to dump
        :return: None
        """
        file.write("// Generated error code to message mapping\n")
        file.write("static QMap<int, QString> error_messages{\n")

        for _, code in cls.get_codes().items():
            if code.message:
                file.write("\t{" + str(code.code) + ', "' + code.message + '"}\n')

        file.write("};\n")

    @classmethod
    def dump_cpp_ts(cls, file: TextIO):
        """
        Dump C++ code defining code message translations to an open file

        :param file: Where to dump
        :return: None
        """
        file.write("// Generated translation string definitions for all defined error messages\n")
        for _, code in cls.get_codes().items():
            if code.message:
                file.write(f'tr("{code.message}");\n')


def unique_codes(cls):
    """
    Class decorator requiring unique code values definition inside the class

    :param cls: Codes class
    :return: Unmodified input class
    """
    used = set()
    for name, code in cls.get_codes().items():
        if code.code in used:
            raise ValueError(f"Code {name} with value {code.code} is deficit!")
        used.add(code.code)

    return cls
