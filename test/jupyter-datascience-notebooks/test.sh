#!/bin/bash
cd "$(dirname "$0")" || exit

# shellcheck source=/dev/null
source test-utils.sh

# Template specific tests
check "usergroups" bash -c 'groups jovyan | sed "s/jovyan ://" | grep jovyan'

# Report result
reportResults
