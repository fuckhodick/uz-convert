"""
Конвертер узбекского текста в новый латинский алфавит (ö ğ ç ş).

Вход: txt, md, csv, tsv, docx, pdf, xlsx, html (латиница, кириллица или смесь).
Выход: текстовый файл .txt в UTF-8.

Запуск:
    python convert.py                      (интерактивно, скрипт всё спросит)
    python convert.py вход.docx            (результат: вход_new.txt)
    python convert.py вход.pdf выход.txt

Для docx, pdf, xlsx нужны библиотеки (без прав администратора):
    pip install --user python-docx pypdf openpyxl
"""
import os
import re
import sys
from html.parser import HTMLParser

# ======================= Настройки =======================
# Все частые варианты апострофа, которые встречаются в узбекских текстах
APOS = "'ʻʼ’‘`´′"
# Нормативный знак для тутук белгиси (меняется в одном месте)
TUTUQ = "'"

# ======================= Конвертация =======================
A = re.escape(APOS)
LETTER = r"[^\W\d_]"

RE_OG = re.compile(rf"([oOgG])[{A}]")                      # o' g' -> ö ğ
RE_CHSH = re.compile(r"([cCsS])[hH]")                      # ch sh -> ç ş
RE_TUTUQ = re.compile(rf"(?<={LETTER})[{A}](?={LETTER})")  # апостроф между буквами

OG = {"o": "ö", "g": "ğ"}
CHSH = {"c": "ç", "s": "ş"}


def _case(src, new):
    return new.upper() if src.isupper() else new


def latin_to_new(text):
    text = RE_OG.sub(lambda m: _case(m.group(1), OG[m.group(1).lower()]), text)
    text = RE_CHSH.sub(lambda m: _case(m.group(1), CHSH[m.group(1).lower()]), text)
    return RE_TUTUQ.sub(TUTUQ, text)


CYR = {
    "а": "a", "б": "b", "в": "v", "г": "g", "д": "d", "ж": "j", "з": "z",
    "и": "i", "й": "y", "к": "k", "л": "l", "м": "m", "н": "n", "о": "o",
    "п": "p", "р": "r", "с": "s", "т": "t", "у": "u", "ф": "f", "х": "x",
    "ч": "ç", "ш": "ş", "ъ": TUTUQ, "ь": "", "э": "e", "ў": "ö",
    "қ": "q", "ғ": "ğ", "ҳ": "h",
    "ё": "yo", "ю": "yu", "я": "ya",
}
VOWELS = set("аеёиоуэюяў")


def cyrillic_to_new(text):
    out = []
    for i, ch in enumerate(text):
        low = ch.lower()
        prev = text[i - 1].lower() if i > 0 else ""
        nxt = text[i + 1] if i + 1 < len(text) else ""

        if low == "е":
            # ye: в начале слова, после гласной и после ъ
            res = "ye" if (not prev.isalpha() or prev in VOWELS or prev == "ъ") else "e"
        elif low == "ц":
            res = "ts" if prev in VOWELS else "s"
        elif low == "ҳ" and prev == "с":
            res = TUTUQ + "h"  # сҳ -> s'h, чтобы не слилось в ş
        elif low in CYR:
            res = CYR[low]
        else:
            out.append(ch)
            continue

        if ch.isupper() and res:
            if len(res) > 1 and (nxt.isupper() or (i > 0 and text[i - 1].isupper())):
                res = res.upper()       # слово ЗАГЛАВНЫМИ: ЁШ -> YOŞ
            else:
                res = res.capitalize()  # Ёш -> Yoş
        out.append(res)
    return "".join(out)


def convert(text):
    # сначала латиница, затем кириллица, иначе «сҳ» спутается с «sh»
    return cyrillic_to_new(latin_to_new(text))


# ======================= Чтение форматов =======================
def need(package, pip_name):
    print(f"\nНе установлена библиотека для этого формата: {package}")
    print(f"Установите командой:  pip install --user {pip_name}")
    sys.exit(1)


def read_text_file(path):
    raw = open(path, "rb").read()
    for enc in ("utf-8-sig", "utf-16", "cp1251"):
        try:
            return raw.decode(enc)
        except (UnicodeDecodeError, UnicodeError):
            continue
    return raw.decode("utf-8", errors="replace")


def read_docx(path):
    try:
        import docx
        from docx.table import Table
        from docx.text.paragraph import Paragraph
    except ImportError:
        need("python-docx", "python-docx")
    d = docx.Document(path)
    lines = []
    for child in d.element.body.iterchildren():
        if child.tag.endswith("}p"):
            lines.append(Paragraph(child, d).text)
        elif child.tag.endswith("}tbl"):
            for row in Table(child, d).rows:
                lines.append("\t".join(c.text for c in row.cells))
    return "\n".join(lines)


def read_pdf(path):
    try:
        from pypdf import PdfReader
    except ImportError:
        need("pypdf", "pypdf")
    pages = [(p.extract_text() or "") for p in PdfReader(path).pages]
    text = "\n\n".join(pages)
    if not text.strip():
        print("\nВ PDF не найден текст: похоже, это скан (картинка).")
        print("Для сканов нужно сначала распознать текст (OCR), скрипт этого не умеет.")
        sys.exit(1)
    return text


def read_xlsx(path):
    try:
        import openpyxl
    except ImportError:
        need("openpyxl", "openpyxl")
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    lines = []
    for ws in wb.worksheets:
        lines.append(f"--- {wb.worksheets.index(ws) + 1} ---")
        for row in ws.iter_rows(values_only=True):
            lines.append("\t".join("" if v is None else str(v) for v in row))
    return "\n".join(lines)


class _HTMLText(HTMLParser):
    BLOCK = {"p", "div", "br", "li", "tr", "h1", "h2", "h3", "h4", "h5", "h6", "table"}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts, self.skip = [], 0

    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style"):
            self.skip += 1
        elif tag in self.BLOCK:
            self.parts.append("\n")

    def handle_endtag(self, tag):
        if tag in ("script", "style"):
            self.skip = max(0, self.skip - 1)
        elif tag in self.BLOCK:
            self.parts.append("\n")

    def handle_data(self, data):
        if not self.skip:
            self.parts.append(data)


def read_html(path):
    p = _HTMLText()
    p.feed(read_text_file(path))
    return re.sub(r"\n{3,}", "\n\n", "".join(p.parts)).strip()


# Формат -> (название, функция чтения, расширения)
FORMATS = [
    ("TXT / MD / LOG (обычный текст)", read_text_file, {".txt", ".md", ".log"}),
    ("CSV / TSV (таблица текстом)", read_text_file, {".csv", ".tsv"}),
    ("DOCX (Word)", read_docx, {".docx"}),
    ("PDF (с текстовым слоем)", read_pdf, {".pdf"}),
    ("XLSX (Excel)", read_xlsx, {".xlsx"}),
    ("HTML (веб-страница)", read_html, {".html", ".htm"}),
]


def detect_format(path):
    ext = os.path.splitext(path)[1].lower()
    for i, (_, _, exts) in enumerate(FORMATS):
        if ext in exts:
            return i
    return None


# ======================= Интерфейс =======================
def clean_path(s):
    return s.strip().strip('"').strip("'")


def ask_format(path):
    idx = detect_format(path)
    print("\nДоступные форматы:")
    for i, (name, _, _) in enumerate(FORMATS, 1):
        print(f"  {i}. {name}")
    if idx is not None:
        ans = input(f"Определён формат: {FORMATS[idx][0]}. "
                    f"Enter, чтобы продолжить, или номер другого формата: ").strip()
        if ans.isdigit() and 1 <= int(ans) <= len(FORMATS):
            idx = int(ans) - 1
    else:
        while idx is None:
            ans = input("Формат не определён. Введите номер формата: ").strip()
            if ans.isdigit() and 1 <= int(ans) <= len(FORMATS):
                idx = int(ans) - 1
    return idx


def process(src, dst, idx):
    text = FORMATS[idx][1](src)
    result = convert(text)
    with open(dst, "w", encoding="utf-8") as f:
        f.write(result)
    return text, result


def interactive():
    print("=== Конвертер узбекского текста в новый алфавит (ö ğ ç ş) ===")
    while True:
        src = clean_path(input("\nПуть к файлу (можно перетащить файл в окно): "))
        if not os.path.isfile(src):
            print("Файл не найден, проверьте путь.")
            continue
        idx = ask_format(src)
        default_dst = os.path.splitext(src)[0] + "_new.txt"
        dst = clean_path(input(f"Куда сохранить [Enter = {default_dst}]: ")) or default_dst
        _, result = process(src, dst, idx)
        print(f"\nГотово: {dst}")
        print("Начало результата:\n" + result[:300])
        if input("\nОбработать ещё один файл? (д/н): ").strip().lower() not in ("д", "y", "да", "yes"):
            break


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    args = sys.argv[1:]
    if not args:
        interactive()
        return
    src = clean_path(args[0])
    idx = detect_format(src)
    if idx is None:
        print("Неизвестный формат файла. Запустите без параметров, и скрипт спросит формат.")
        sys.exit(1)
    dst = clean_path(args[1]) if len(args) > 1 else os.path.splitext(src)[0] + "_new.txt"
    process(src, dst, idx)
    print("Готово:", dst)


if __name__ == "__main__":
    main()
