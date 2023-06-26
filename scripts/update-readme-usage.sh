#!/bin/bash
#------------------------------------------------------------------------------
# macedon [CLI web service availability verifier]
# (c) 2023 A. Shavykin <0.delameter@gmail.com>
#------------------------------------------------------------------------------

sed < README.md -Ee '/^\s+Options:$/q' \
    > README.md.new
COLUMNS=130 ./run.sh --help \
    | tac | sed -nEe 's/^Options://; Tp; q; :p p' \
    | tac | sed -nEe 's/^/    /; p; /^\s+--help/q' \
    >> README.md.new
tac < README.md \
    | sed -nEe '/^\s+--help/q; p' \
    | tac \
    >> README.md.new
mv README.md.new README.md
