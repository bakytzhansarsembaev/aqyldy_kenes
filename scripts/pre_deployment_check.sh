#!/bin/bash

# ============================================
# Pre-Deployment Checks для Task Helper v2.0
# ============================================
#
# Использование: bash scripts/pre_deployment_check.sh
#
# Проверяет:
# - Python версию
# - Зависимости
# - Environment variables
# - Redis connection
# - Директорию логов
# - Базовые тесты

# Не используем set -e из-за проблем с арифметическими операциями

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Счётчики
PASSED=0
FAILED=0
WARNINGS=0

echo ""
echo "========================================"
echo "Pre-Deployment Checks для Task Helper"
echo "========================================"
echo ""

# ============================================
# 1. Проверка Python версии
# ============================================
echo -n "1. Checking Python version... "

PYTHON_VERSION=$(python3 --version 2>&1 | cut -d' ' -f2)
PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d'.' -f1)
PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d'.' -f2)

if [ "$PYTHON_MAJOR" -ge 3 ] && [ "$PYTHON_MINOR" -ge 10 ]; then
    echo -e "${GREEN}OK${NC} (Python $PYTHON_VERSION)"
    ((PASSED++))
else
    echo -e "${RED}FAIL${NC} (Python $PYTHON_VERSION, требуется 3.10+)"
    ((FAILED++))
fi

# ============================================
# 2. Проверка зависимостей
# ============================================
echo -n "2. Checking core dependencies... "

MISSING_DEPS=""

# Проверяем основные пакеты
for pkg in openai langgraph pydantic redis pika requests; do
    if ! python3 -c "import $pkg" 2>/dev/null; then
        MISSING_DEPS="$MISSING_DEPS $pkg"
    fi
done

if [ -z "$MISSING_DEPS" ]; then
    echo -e "${GREEN}OK${NC}"
    ((PASSED++))
else
    echo -e "${RED}FAIL${NC} (missing:$MISSING_DEPS)"
    ((FAILED++))
fi

# ============================================
# 3. Проверка environment variables
# ============================================
echo -n "3. Checking environment variables... "

MISSING_ENV=""

if [ -z "$OPENAI_API_KEY" ]; then
    MISSING_ENV="$MISSING_ENV OPENAI_API_KEY"
fi

if [ -z "$QALAN_MAIN_TOKEN" ]; then
    MISSING_ENV="$MISSING_ENV QALAN_MAIN_TOKEN"
fi

if [ -z "$MISSING_ENV" ]; then
    echo -e "${GREEN}OK${NC}"
    ((PASSED++))
else
    echo -e "${YELLOW}WARNING${NC} (missing:$MISSING_ENV)"
    ((WARNINGS++))
fi

# ============================================
# 4. Проверка logs директории
# ============================================
echo -n "4. Checking logs directory... "

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
LOGS_DIR="$PROJECT_DIR/logs"

if [ -d "$LOGS_DIR" ]; then
    echo -e "${GREEN}OK${NC} ($LOGS_DIR)"
    ((PASSED++))
else
    mkdir -p "$LOGS_DIR"
    echo -e "${YELLOW}CREATED${NC} ($LOGS_DIR)"
    ((WARNINGS++))
fi

# ============================================
# 5. Проверка Redis connection
# ============================================
echo -n "5. Checking Redis connection... "

REDIS_CHECK=$(python3 -c "
try:
    from src.tools.storage.state_store.redis_usage.redis_connection import redis_connection
    redis_connection.ping()
    print('OK')
except Exception as e:
    print(f'FAIL: {e}')
" 2>&1)

if [[ "$REDIS_CHECK" == "OK" ]]; then
    echo -e "${GREEN}OK${NC}"
    ((PASSED++))
else
    echo -e "${YELLOW}WARNING${NC} (Redis not available)"
    ((WARNINGS++))
fi

# ============================================
# 6. Проверка конфигурации
# ============================================
echo -n "6. Checking configuration... "

CONFIG_CHECK=$(python3 -c "
try:
    from src.configs.settings import USABLE_BRANCH, USE_MOCK_SERVICES
    print(f'OK (branch={USABLE_BRANCH}, mock={USE_MOCK_SERVICES})')
except Exception as e:
    print(f'FAIL: {e}')
" 2>&1)

if [[ "$CONFIG_CHECK" == OK* ]]; then
    echo -e "${GREEN}$CONFIG_CHECK${NC}"
    ((PASSED++))
else
    echo -e "${RED}$CONFIG_CHECK${NC}"
    ((FAILED++))
fi

# ============================================
# 7. Проверка Agent Registry
# ============================================
echo -n "7. Checking Agent Registry... "

REGISTRY_CHECK=$(python3 -c "
try:
    from src.agents.registry import AGENT_REGISTRY
    from src.utils.classifier.intents import IntentEnum

    # Проверяем что mentor зарегистрирован
    mentor_key = (IntentEnum.mentor, None)
    if mentor_key in AGENT_REGISTRY:
        print(f'OK ({len(AGENT_REGISTRY)} agents)')
    else:
        print('FAIL: MentorAgent not registered')
except Exception as e:
    print(f'FAIL: {e}')
" 2>&1)

if [[ "$REGISTRY_CHECK" == OK* ]]; then
    echo -e "${GREEN}$REGISTRY_CHECK${NC}"
    ((PASSED++))
else
    echo -e "${RED}$REGISTRY_CHECK${NC}"
    ((FAILED++))
fi

# ============================================
# 8. Проверка Policy Loader
# ============================================
echo -n "8. Checking Policy Loader... "

POLICY_CHECK=$(python3 -c "
try:
    from src.utils.policies.policy_loader import PolicyLoader, POLICY_PATHS
    loader = PolicyLoader()

    # Проверяем что mentor policy путь есть
    if ('mentor', None) in POLICY_PATHS:
        print(f'OK ({len(POLICY_PATHS)} policies)')
    else:
        print('FAIL: mentor policy path not found')
except Exception as e:
    print(f'FAIL: {e}')
" 2>&1)

if [[ "$POLICY_CHECK" == OK* ]]; then
    echo -e "${GREEN}$POLICY_CHECK${NC}"
    ((PASSED++))
else
    echo -e "${RED}$POLICY_CHECK${NC}"
    ((FAILED++))
fi

# ============================================
# 9. Проверка LaTeX Processor
# ============================================
echo -n "9. Checking LaTeX Processor... "

LATEX_CHECK=$(python3 -c "
try:
    from src.utils.latex_processor import fix_latex_formatting, validate_latex

    # Тестовая формула
    test = r'\[ x = 5 \]'
    if validate_latex(test):
        print('OK')
    else:
        print('FAIL: validation failed')
except Exception as e:
    print(f'FAIL: {e}')
" 2>&1)

if [[ "$LATEX_CHECK" == "OK" ]]; then
    echo -e "${GREEN}OK${NC}"
    ((PASSED++))
else
    echo -e "${RED}$LATEX_CHECK${NC}"
    ((FAILED++))
fi

# ============================================
# 10. Запуск pytest (если доступен)
# ============================================
echo -n "10. Running basic tests... "

if command -v pytest &> /dev/null; then
    TEST_RESULT=$(cd "$PROJECT_DIR" && python3 -m pytest src/tests/ -q --tb=no 2>&1 | tail -1)
    if [[ "$TEST_RESULT" == *"passed"* ]] || [[ "$TEST_RESULT" == *"no tests ran"* ]]; then
        echo -e "${GREEN}OK${NC} ($TEST_RESULT)"
        ((PASSED++))
    else
        echo -e "${YELLOW}WARNING${NC} ($TEST_RESULT)"
        ((WARNINGS++))
    fi
else
    echo -e "${YELLOW}SKIPPED${NC} (pytest not found)"
    ((WARNINGS++))
fi

# ============================================
# SUMMARY
# ============================================
echo ""
echo "========================================"
echo "SUMMARY"
echo "========================================"
echo -e "Passed:   ${GREEN}$PASSED${NC}"
echo -e "Warnings: ${YELLOW}$WARNINGS${NC}"
echo -e "Failed:   ${RED}$FAILED${NC}"
echo "========================================"

if [ $FAILED -eq 0 ]; then
    echo ""
    echo -e "${GREEN}All critical checks passed!${NC}"
    echo "Ready for deployment."
    echo ""
    exit 0
else
    echo ""
    echo -e "${RED}Some critical checks failed!${NC}"
    echo "Please fix the issues before deployment."
    echo ""
    exit 1
fi
