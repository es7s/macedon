#-------------------------------------------------------------------------------
# es7s/core
# (c) 2021-2022 A. Shavykin <0.delameter@gmail.com>
#-------------------------------------------------------------------------------

PYDEPS_PATH="${1:?pydeps path required}"
PROJECT_NAME="${2:?Project name required}"
OUTPUT_PATH="${3:?Output path required}"

$PYDEPS_PATH "${PROJECT_NAME}" \
    --rmprefix "${PROJECT_NAME}". \
    --start-color 120 \
    --only "${PROJECT_NAME}" \
    -o "${OUTPUT_PATH}"/structure.svg

$PYDEPS_PATH "${PROJECT_NAME}" \
    --rmprefix "${PROJECT_NAME}". \
    --start-color 120 \
    --show-cycle \
    --no-show \
    -o "${OUTPUT_PATH}"/cycles.svg

$PYDEPS_PATH "${PROJECT_NAME}" \
    --start-color 0 \
    --max-bacon 3 \
    --max-mod 0 \
    --max-cluster 100 \
    --keep \
    --no-show \
    -o "${OUTPUT_PATH}"/imports-deep.svg

$PYDEPS_PATH "${PROJECT_NAME}" \
    --start-color 0 \
    --max-bacon 3 \
    --cluster \
    --collapse \
    --no-show \
    -o "${OUTPUT_PATH}"/imports-cross.svg

$PYDEPS_PATH "${PROJECT_NAME}" \
    --start-color 0 \
    --max-bacon 12 \
    --max-mod 1 \
    --cluster \
    --collapse \
    --no-show \
    -o "${OUTPUT_PATH}"/imports-far.svg
