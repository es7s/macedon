# -----------------------------------------------------------------------------
#  macedon [CLI web service availability verifier]
#  (c) 2023 A. Shavykin <0.delameter@gmail.com>
# -----------------------------------------------------------------------------
from __future__ import annotations
import sys

import click
import pytermor as pt
import typing as t

from ._common import Options

_stdout: IoProxy | None = None
_stderr: IoProxy | None = None


def get_stdout(require=True) -> IoProxy | None:
    if not _stdout:
        if require:
            raise Exception("Stdout proxy is not initialized")
        return None
    return _stdout


def get_stderr(require=True) -> IoProxy | None:
    if not _stderr:
        if require:
            raise Exception("Stderr proxy is not initialized")
        return None
    return _stderr


def init_io(options: Options) -> tuple[IoProxy, IoProxy]:
    global _stdout, _stderr
    if _stdout:
        raise RuntimeError("Stdout proxy is already initialized")
    if _stderr:
        raise RuntimeError("Stderr proxy is already initialized")

    _stdout = IoProxy(options.color, sys.stdout)
    _stderr = IoProxy(options.color, sys.stderr)
    pt.RendererManager.set_default(_stdout.renderer)
    return _stdout, _stderr


def destroy_io():
    global _stdout, _stderr
    if _stdout:
        _stdout.destroy()
    if _stderr:
        _stderr.destroy()
    _stdout = _stderr = None


class IoProxy:
    def __init__(self, color_option: bool, io: t.IO):
        self._color = color_option
        self._renderer = self._make_renderer(io)
        self._io = io
        self._is_stderr = io == sys.stderr
        self._broken = False
        self._click_available = False

        try:
            import click

            self._click_available = isinstance(click.echo, t.Callable)
        except ImportError:
            pass

    @property
    def renderer(self) -> pt.IRenderer:
        return self._renderer

    def render(self, string: pt.RT = "", fmt: pt.FT = None) -> str:
        return pt.render(string, fmt, self._renderer)

    def echo_rendered(self, string: pt.RT = "", fmt: pt.FT = None):
        self.echo(self.render(string, fmt))

    def echo(self, string: str = "", newline: bool = True):
        try:
            if self._click_available:
                click.echo(string, file=self._io, color=self._color, nl=newline)
            else:
                print(
                    string,
                    file=self._io,
                    end=("\n" if newline else ""),
                    flush=not bool(string),
                )
        except BrokenPipeError:
            self._broken = True
            self._pacify_flush_wrapper()

    def destroy(self):
        self._io = None

    def _make_renderer(self, io: t.IO) -> pt.IRenderer:
        if self._color is False:
            return pt.renderer.NoOpRenderer()
        return pt.SgrRenderer(self._output_mode, io)

    def _pacify_flush_wrapper(self):
        sys.stdout = t.cast(t.TextIO, click.utils.PacifyFlushWrapper(sys.stdout))
        sys.stderr = t.cast(t.TextIO, click.utils.PacifyFlushWrapper(sys.stderr))

    @property
    def _output_mode(self) -> pt.OutputMode:
        if self._color is None:
            return pt.OutputMode.AUTO
        if self._color:
            return pt.OutputMode.TRUE_COLOR
        return pt.OutputMode.NO_ANSI
