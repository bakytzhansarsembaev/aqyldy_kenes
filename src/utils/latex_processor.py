"""
LaTeX Processor для обработки математических формул в ответах агента.

Поддерживает:
- Исправление спецсимволов
- Обработка блочных \\[ ... \\] и строчных \\( ... \\) формул
- Валидация и санитизация формул
"""

import re
from typing import List, Tuple


# Список поддерживаемых LaTeX команд
LATEX_COMMANDS = [
    "frac", "tfrac", "dfrac", "sqrt", "sum", "int", "lim", "infty",
    "cdot", "times", "div", "pm", "ne", "approx", "leq", "geq",
    "left", "right", "begin", "end", "text", "textit", "textbf",
    "alpha", "beta", "gamma", "delta", "pi", "theta", "lambda",
    "sin", "cos", "tan", "log", "ln", "lg",
    "angle", "degree", "overline", "underline", "vec",
    "quad", "qquad", "space", "hspace", "vspace",
    "mathbb", "mathbf", "mathrm", "mathcal", "mathit",
    "rightarrow", "leftarrow", "Rightarrow", "Leftarrow",
    "subset", "supset", "subseteq", "supseteq", "in", "notin",
    "forall", "exists", "partial", "nabla"
]

# Запрещённые команды (могут использоваться для инъекций)
FORBIDDEN_COMMANDS = [
    "input", "include", "write", "openout",
    "closeout", "def", "gdef", "edef", "xdef",
    "newcommand", "renewcommand", "catcode"
]


def fix_latex_formatting(text: str) -> str:
    """
    Исправить LaTeX форматирование в ответе агента.

    Обрабатывает:
    - Спецсимволы (\\a, \\b, \\f, \\t, \\r)
    - Переносы строк внутри формул
    - Ведущие слэши перед командами

    Args:
        text: Текст с LaTeX формулами

    Returns:
        Исправленный текст
    """
    if not text:
        return text

    # ============================================
    # 1. Замена спецсимволов
    # ============================================
    replacements = {
        chr(7): '\\a',   # Bell
        chr(8): '\\b',   # Backspace
        chr(12): '\\f',  # Form feed
        chr(9): '\\t',   # Tab
        chr(13): '\\r',  # Carriage return
    }

    for old, new in replacements.items():
        if old in text:
            text = text.replace(old, new)

    # ============================================
    # 2. Обработка блоков LaTeX
    # ============================================
    def fix_newlines_in_latex(match):
        """Заменить \\n на \\\\\\\\ внутри формул"""
        content = match.group(0)
        # Заменяем переносы строк на LaTeX-совместимые
        return content.replace('\n', ' \\\\ ').replace(chr(10), ' \\\\ ')

    # Паттерн для блочных \\[ ... \\] формул
    block_pattern = r'\\\[.*?\\\]'
    text = re.sub(block_pattern, fix_newlines_in_latex, text, flags=re.DOTALL)

    # Паттерн для строчных \\( ... \\) формул
    inline_pattern = r'\\\(.*?\\\)'
    text = re.sub(inline_pattern, fix_newlines_in_latex, text, flags=re.DOTALL)

    # ============================================
    # 3. Санитизация опасных команд
    # ============================================
    text = sanitize_latex(text)

    return text


def validate_latex(text: str) -> bool:
    """
    Проверить, содержит ли текст LaTeX формулы

    Args:
        text: Текст для проверки

    Returns:
        True если найдены формулы, False иначе
    """
    if not text:
        return False

    # Проверяем наличие блочных или строчных формул
    block_pattern = r'\\\[.*?\\\]'
    inline_pattern = r'\\\(.*?\\\)'
    dollar_pattern = r'\$[^$]+\$'
    double_dollar_pattern = r'\$\$[^$]+\$\$'

    patterns = [block_pattern, inline_pattern, dollar_pattern, double_dollar_pattern]

    for pattern in patterns:
        if re.search(pattern, text, re.DOTALL):
            return True

    return False


def extract_latex_formulas(text: str) -> List[str]:
    """
    Извлечь все LaTeX формулы из текста

    Args:
        text: Текст с формулами

    Returns:
        Список формул
    """
    if not text:
        return []

    formulas = []

    # Блочные формулы \\[ ... \\]
    block_pattern = r'\\\[.*?\\\]'
    formulas.extend(re.findall(block_pattern, text, re.DOTALL))

    # Строчные формулы \\( ... \\)
    inline_pattern = r'\\\(.*?\\\)'
    formulas.extend(re.findall(inline_pattern, text, re.DOTALL))

    # $ ... $ формулы
    dollar_pattern = r'\$[^$]+\$'
    formulas.extend(re.findall(dollar_pattern, text, re.DOTALL))

    # $$ ... $$ формулы
    double_dollar_pattern = r'\$\$[^$]+\$\$'
    formulas.extend(re.findall(double_dollar_pattern, text, re.DOTALL))

    return formulas


def sanitize_latex(text: str) -> str:
    """
    Санитизация LaTeX текста для безопасности.
    Удаляет потенциально опасные команды.

    Args:
        text: Текст с LaTeX

    Returns:
        Безопасный текст
    """
    if not text:
        return text

    for cmd in FORBIDDEN_COMMANDS:
        # Паттерн для команды с необязательными аргументами
        pattern = r'\\' + cmd + r'(\s*\{[^}]*\}|\s*\[[^\]]*\])*'
        text = re.sub(pattern, '', text, flags=re.IGNORECASE)

    return text


def format_math_expression(expression: str) -> str:
    """
    Форматировать математическое выражение в LaTeX.

    Args:
        expression: Математическое выражение (например, "x^2 + 2x + 1 = 0")

    Returns:
        Форматированное выражение в LaTeX
    """
    # Обёртываем в строчную формулу если ещё не обёрнуто
    if not (expression.startswith('\\(') or expression.startswith('\\[') or
            expression.startswith('$')):
        return f'\\( {expression} \\)'
    return expression


def has_balanced_delimiters(text: str) -> Tuple[bool, str]:
    """
    Проверить сбалансированность LaTeX разделителей.

    Args:
        text: Текст для проверки

    Returns:
        Tuple (is_balanced, error_message)
    """
    # Проверяем парность \\[ и \\]
    open_block = text.count('\\[')
    close_block = text.count('\\]')
    if open_block != close_block:
        return False, f"Несбалансированные \\[ \\]: открытых {open_block}, закрытых {close_block}"

    # Проверяем парность \\( и \\)
    open_inline = text.count('\\(')
    close_inline = text.count('\\)')
    if open_inline != close_inline:
        return False, f"Несбалансированные \\( \\): открытых {open_inline}, закрытых {close_inline}"

    # Проверяем парность $
    dollars = text.count('$')
    # Учитываем что $$ считается как один разделитель
    double_dollars = text.count('$$')
    single_dollars = dollars - (double_dollars * 2)
    if single_dollars % 2 != 0:
        return False, f"Нечётное количество одинарных $: {single_dollars}"

    return True, "OK"


def count_formulas(text: str) -> int:
    """
    Подсчитать количество LaTeX формул в тексте.

    Args:
        text: Текст с формулами

    Returns:
        Количество формул
    """
    return len(extract_latex_formulas(text))


# ============================================
# Примеры использования
# ============================================

if __name__ == "__main__":
    # Пример 1: Простая формула
    text1 = "Решение: \\[ x = \\frac{-b \\pm \\sqrt{b^2 - 4ac}}{2a} \\]"
    print("Пример 1 - Простая формула:")
    print(f"  До: {text1}")
    print(f"  После: {fix_latex_formatting(text1)}")
    print(f"  Валидна: {validate_latex(text1)}")
    print()

    # Пример 2: Формула с переносами
    text2 = """Используй формулу: \\[
    \\frac{a}{b} = c
    \\]"""
    print("Пример 2 - Формула с переносами:")
    print(f"  До: {repr(text2)}")
    print(f"  После: {repr(fix_latex_formatting(text2))}")
    print()

    # Пример 3: Строчная формула
    text3 = "Квадратный корень: \\( \\sqrt{25} = 5 \\)"
    print("Пример 3 - Строчная формула:")
    print(f"  До: {text3}")
    print(f"  После: {fix_latex_formatting(text3)}")
    print(f"  Формулы: {extract_latex_formulas(text3)}")
    print()

    # Пример 4: Проверка баланса
    text4 = "\\[ x = 1 \\] и \\( y = 2 \\)"
    balanced, msg = has_balanced_delimiters(text4)
    print(f"Пример 4 - Баланс: {balanced}, {msg}")
    print()

    # Пример 5: Подсчёт формул
    text5 = "Формула 1: \\[ a \\], формула 2: \\( b \\), формула 3: $c$"
    print(f"Пример 5 - Количество формул: {count_formulas(text5)}")
