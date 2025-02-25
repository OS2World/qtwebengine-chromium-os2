# Copyright 2019 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import os.path
import subprocess
import sys

_clang_format_command_path = None
_gn_command_path = None


def init(root_src_dir):
    global _clang_format_command_path
    global _gn_command_path

    assert _clang_format_command_path is None
    assert _gn_command_path is None

    root_src_dir = os.path.abspath(root_src_dir)

    # Determine //buildtools/<platform>/ directory
    if sys.platform.startswith("linux"):
        platform = "linux64"
        exe_suffix = ""
    elif sys.platform.startswith("darwin"):
        platform = "mac"
        exe_suffix = ""
    elif sys.platform.startswith(("cygwin", "win", "os2")):
        platform = "win"
        exe_suffix = ".exe"
    elif sys.platform.startswith(("os2")):
        platform = "os2"
        exe_suffix = ".exe"
    else:
        assert False, "Unknown platform: {}".format(sys.platform)
    buildtools_platform_dir = os.path.join(root_src_dir, "buildtools",
                                           platform)

    # //buildtools/<platform>/clang-format
    _clang_format_command_path = os.path.join(
        buildtools_platform_dir, "clang-format{}".format(exe_suffix))

    # //buildtools/<platform>/gn
    _gn_command_path = os.path.join(buildtools_platform_dir,
                                    "gn{}".format(exe_suffix))


def auto_format(contents, filename):
    assert isinstance(filename, str)

    _, ext = os.path.splitext(filename)
    if ext in (".gn", ".gni"):
        return gn_format(contents, filename)

    return clang_format(contents, filename)


def clang_format(contents, filename=None):
    command_line = [_clang_format_command_path]
    if filename is not None:
        command_line.append('-assume-filename={}'.format(filename))

    return _invoke_format_command(command_line, filename, contents)


def gn_format(contents, filename=None):
    command_line = [_gn_command_path, "format", "--stdin"]
    if filename is not None:
        command_line.append('-assume-filename={}'.format(filename))

    return _invoke_format_command(command_line, filename, contents)


def _invoke_format_command(command_line, filename, contents):
    proc = subprocess.Popen(
        command_line, stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    stdout_output, stderr_output = proc.communicate(input=contents)
    exit_code = proc.wait()

    return StyleFormatResult(
        stdout_output=stdout_output,
        stderr_output=stderr_output,
        exit_code=exit_code,
        filename=filename)


class StyleFormatResult(object):
    def __init__(self, stdout_output, stderr_output, exit_code, filename):
        self._stdout_output = stdout_output
        self._stderr_output = stderr_output
        self._exit_code = exit_code
        self._filename = filename

    @property
    def did_succeed(self):
        return self._exit_code == 0

    @property
    def contents(self):
        assert self.did_succeed
        return self._stdout_output

    @property
    def error_message(self):
        return self._stderr_output

    @property
    def filename(self):
        return self._filename
