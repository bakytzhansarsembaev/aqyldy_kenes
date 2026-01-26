import re

def fix_latex_formatting(text: str) -> str:
    """Исправить LaTeX форматирование в ответе агента"""
    
    # Замена спецсимволов
    replacements = {
        chr(7): '\\a',
        chr(8): '\\b', 
        chr(12): '\\f',
        chr(9): '\\t',
        chr(13): '\\r',
        "\'": '"'
    }
    
    for old, new in replacements.items():
        if old in text:
            text = text.replace(old, new)
    
    # Обработка блоков LaTeX
    def fix_newlines_in_latex(match):
        content = match.group(0)
        return content.replace('\n', '\\\\').replace(chr(10), '\\\\')
    
    pattern = r'(\\\[.*?\\\]|\\\(.*?\\\))'
    text = re.sub(pattern, fix_newlines_in_latex, text, flags=re.DOTALL)
    
    return fr'{text}'