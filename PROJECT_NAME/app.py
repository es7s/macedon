# -----------------------------------------------------------------------------
# *PROJECT_NAME [*PROJECT_DESCRIPTION]
# (C) *CYR A. Shavykin <0.delameter@gmail.com>
# -----------------------------------------------------------------------------
"""
SYNOPSIS
    *PROJECT_NAME
    *PROJECT_NAME --help

Prints out this help or crashes with NotImplementedError.

ARGUMENTS
  No.
"""
import sys


# noinspection PyMethodMayBeStatic
class App:
    def run(self):
        try:
            self._entrypoint()
        except Exception as e:
            self._print_exception(e)
            self._exit(1)
        self._exit(0)

    def _entrypoint(self):
        if {'-h', '--help'}.intersection(sys.argv):
            self._print_usage()
            return

        self._parse_args()
        raise NotImplementedError('NO')

    def _parse_args(self):
        pass

    def _print_usage(self):
        print(__doc__)

    def _print_exception(self, e):
        print(str(e), file=sys.stderr)

    def _exit(self, code: int):
        print()
        exit(code)


if __name__ == '__main__':
    App().run()
