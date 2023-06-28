#!/bin/bash
cd "$(dirname "$0")" || exit

# shellcheck source=/dev/null
source test-utils.sh

# Template specific tests
check "dart exists" dart --version

# Report result
reportResults
