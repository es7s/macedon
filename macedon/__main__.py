# -----------------------------------------------------------------------------
#  macedon [CLI web service availability verifier]
#  (c) 2022-2023 A. Shavykin <0.delameter@gmail.com>
# -----------------------------------------------------------------------------

from .entrypoint import invoke as entrypoint_fn


def main():
    entrypoint_fn()


if __name__ == "__main__":
    main()
