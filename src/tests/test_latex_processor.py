"""
Тесты для LaTeX Processor.

Запуск: pytest src/tests/test_latex_processor.py -v
"""

import pytest
from src.utils.latex_processor import (
    fix_latex_formatting,
    validate_latex,
    extract_latex_formulas,
    sanitize_latex,
    has_balanced_delimiters,
    count_formulas,
    format_math_expression
)


class TestValidateLatex:
    """Тесты валидации LaTeX"""

    def test_validate_block_formula(self):
        """Тест распознавания блочной формулы"""
        text = "Формула: \\[ x^2 + y^2 = r^2 \\]"
        assert validate_latex(text) is True

    def test_validate_inline_formula(self):
        """Тест распознавания строчной формулы"""
        text = "Корень: \\( \\sqrt{25} = 5 \\)"
        assert validate_latex(text) is True

    def test_validate_dollar_formula(self):
        """Тест распознавания $ формулы"""
        text = "Уравнение: $x + y = z$"
        assert validate_latex(text) is True

    def test_validate_double_dollar_formula(self):
        """Тест распознавания $$ формулы"""
        text = "Формула: $$\\frac{a}{b}$$"
        assert validate_latex(text) is True

    def test_validate_no_latex(self):
        """Тест отсутствия LaTeX"""
        text = "Обычный текст без формул"
        assert validate_latex(text) is False

    def test_validate_empty_string(self):
        """Тест пустой строки"""
        assert validate_latex("") is False
        assert validate_latex(None) is False


class TestFixLatexFormatting:
    """Тесты исправления форматирования"""

    def test_fix_simple_formula(self):
        """Тест простой формулы"""
        text = "\\[ x = 5 \\]"
        fixed = fix_latex_formatting(text)
        assert "x = 5" in fixed

    def test_fix_newlines(self):
        """Тест исправления переносов строк"""
        text = "\\[\n x = 5 \n\\]"
        fixed = fix_latex_formatting(text)
        # Переносы должны быть заменены на LaTeX-совместимые
        assert fixed is not None

    def test_fix_special_chars(self):
        """Тест замены спецсимволов"""
        text = "text\twith\ttabs"
        fixed = fix_latex_formatting(text)
        assert fixed is not None

    def test_fix_empty_string(self):
        """Тест пустой строки"""
        assert fix_latex_formatting("") == ""
        assert fix_latex_formatting(None) is None


class TestExtractFormulas:
    """Тесты извлечения формул"""

    def test_extract_single_block(self):
        """Тест извлечения одной блочной формулы"""
        text = "Формула: \\[ x = 1 \\]"
        formulas = extract_latex_formulas(text)
        assert len(formulas) == 1
        assert "x = 1" in formulas[0]

    def test_extract_multiple_formulas(self):
        """Тест извлечения нескольких формул"""
        text = "Формулы: \\[ x = 1 \\] и \\( y = 2 \\)"
        formulas = extract_latex_formulas(text)
        assert len(formulas) == 2

    def test_extract_mixed_types(self):
        """Тест извлечения разных типов формул"""
        text = "\\[ a \\], \\( b \\), $c$"
        formulas = extract_latex_formulas(text)
        assert len(formulas) == 3

    def test_extract_empty(self):
        """Тест пустого текста"""
        assert extract_latex_formulas("") == []
        assert extract_latex_formulas(None) == []
        assert extract_latex_formulas("no formulas here") == []


class TestSanitizeLatex:
    """Тесты санитизации LaTeX"""

    def test_sanitize_dangerous_input(self):
        """Тест удаления опасных команд"""
        dangerous = "\\[ \\input{secret.tex} x = 5 \\]"
        safe = sanitize_latex(dangerous)
        assert "input" not in safe.lower()

    def test_sanitize_include_command(self):
        """Тест удаления \\include"""
        dangerous = "\\include{file}"
        safe = sanitize_latex(dangerous)
        assert "include" not in safe.lower()

    def test_sanitize_def_command(self):
        """Тест удаления \\def"""
        dangerous = "\\def\\foo{bar}"
        safe = sanitize_latex(dangerous)
        assert "def" not in safe.lower()

    def test_sanitize_safe_content(self):
        """Тест что безопасный контент не изменяется"""
        safe_text = "\\[ \\frac{a}{b} + \\sqrt{c} \\]"
        result = sanitize_latex(safe_text)
        assert "frac" in result
        assert "sqrt" in result


class TestBalancedDelimiters:
    """Тесты проверки баланса разделителей"""

    def test_balanced_block(self):
        """Тест сбалансированных \\[ \\]"""
        text = "\\[ x = 1 \\]"
        balanced, msg = has_balanced_delimiters(text)
        assert balanced is True

    def test_balanced_inline(self):
        """Тест сбалансированных \\( \\)"""
        text = "\\( y = 2 \\)"
        balanced, msg = has_balanced_delimiters(text)
        assert balanced is True

    def test_unbalanced_block(self):
        """Тест несбалансированных \\["""
        text = "\\[ x = 1"
        balanced, msg = has_balanced_delimiters(text)
        assert balanced is False

    def test_multiple_balanced(self):
        """Тест нескольких сбалансированных формул"""
        text = "\\[ a \\] и \\( b \\) и \\[ c \\]"
        balanced, msg = has_balanced_delimiters(text)
        assert balanced is True


class TestCountFormulas:
    """Тесты подсчёта формул"""

    def test_count_single(self):
        """Тест подсчёта одной формулы"""
        text = "\\[ x = 1 \\]"
        assert count_formulas(text) == 1

    def test_count_multiple(self):
        """Тест подсчёта нескольких формул"""
        text = "\\[ a \\], \\( b \\), $c$"
        assert count_formulas(text) == 3

    def test_count_zero(self):
        """Тест отсутствия формул"""
        assert count_formulas("no formulas") == 0
        assert count_formulas("") == 0


class TestFormatMathExpression:
    """Тесты форматирования математических выражений"""

    def test_format_plain_expression(self):
        """Тест форматирования простого выражения"""
        expr = "x^2 + 1"
        formatted = format_math_expression(expr)
        assert formatted.startswith("\\(")
        assert formatted.endswith("\\)")

    def test_format_already_formatted(self):
        """Тест уже отформатированного выражения"""
        expr = "\\( x = 5 \\)"
        formatted = format_math_expression(expr)
        assert formatted == expr


class TestRealWorldExamples:
    """Тесты с реальными примерами из математики"""

    def test_quadratic_formula(self):
        """Тест квадратной формулы"""
        text = "Корни уравнения: \\[ x = \\frac{-b \\pm \\sqrt{b^2-4ac}}{2a} \\]"
        assert validate_latex(text) is True
        fixed = fix_latex_formatting(text)
        assert "frac" in fixed
        assert "sqrt" in fixed

    def test_pythagorean_theorem(self):
        """Тест теоремы Пифагора"""
        text = "Теорема: \\( a^2 + b^2 = c^2 \\)"
        assert validate_latex(text) is True
        formulas = extract_latex_formulas(text)
        assert len(formulas) == 1

    def test_trigonometry(self):
        """Тест тригонометрии"""
        text = "Синус: \\[ \\sin^2(x) + \\cos^2(x) = 1 \\]"
        assert validate_latex(text) is True
        fixed = fix_latex_formatting(text)
        assert "sin" in fixed
        assert "cos" in fixed

    def test_fraction_with_newlines(self):
        """Тест дроби с переносами"""
        text = """Дробь: \\[
            \\frac{a}{b}
        \\]"""
        assert validate_latex(text) is True
        fixed = fix_latex_formatting(text)
        assert "frac" in fixed
