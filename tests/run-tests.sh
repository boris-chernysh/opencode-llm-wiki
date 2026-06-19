#!/bin/bash
# run-tests.sh — запуск всех тестов llm-wiki
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(dirname "$SCRIPT_DIR")"
TEST_VAULT="/tmp/test-vault-$$"

cleanup() { rm -rf "$TEST_VAULT"; }
trap cleanup EXIT

echo "=== Настройка тестового vault ==="

mkdir -p "$TEST_VAULT"
cp -r "$SCRIPT_DIR/fixtures/vault/"* "$TEST_VAULT/"
cp -r "$REPO_ROOT/wiki/" "$TEST_VAULT/wiki/"

echo "Тестовый vault: $TEST_VAULT"
echo ""

PASS=0
FAIL=0
FAILURES=""

run_test() {
    local test_file="$1"
    local test_name
    test_name="$(basename "$test_file" .py)"
    echo -n "$test_name ... "
    if python3 "$test_file" "$TEST_VAULT" 2>&1; then
        echo "PASS"
        PASS=$((PASS + 1))
    else
        echo "FAIL"
        FAIL=$((FAIL + 1))
        FAILURES="$FAILURES $test_name"
    fi
}

for test in "$SCRIPT_DIR"/test_*.py; do
    [ -f "$test" ] || continue
    run_test "$test"
done

echo ""
echo "=== Результаты: $PASS PASS, $FAIL FAIL ==="
if [ "$FAIL" -gt 0 ]; then
    echo "Провалены:$FAILURES"
    exit 1
fi
exit 0
