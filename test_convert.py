"""
Тесты конвертера. Запуск:  python test_convert.py
Если какой-то случай не проходит, скрипт покажет, что получилось и что ожидалось.
Новые случаи добавляйте в таблицу CASES: (вход, ожидаемый результат).
"""
import unittest

from convert import convert

CASES = [
    # --- латиница: o' g' и все виды апострофа ---
    ("O'zbekiston", "Özbekiston"),
    ("g'oya", "ğoya"),
    ("G'ALABA", "ĞALABA"),
    ("O'ZBEKISTON", "ÖZBEKISTON"),
    ("mo`jiza", "möjiza"),
    ("g‘oya", "ğoya"),
    ("Oʻzbek", "Özbek"),
    ("«O'zbek»", "«Özbek»"),
    # --- латиница: ch и sh в любом регистре ---
    ("shahar", "şahar"),
    ("Shahar", "Şahar"),
    ("SHAHAR", "ŞAHAR"),
    ("choy", "çoy"),
    ("Choy", "Çoy"),
    ("CHOY", "ÇOY"),
    ("mashina", "maşina"),
    ("shoshilinch", "şoşilinç"),
    # --- латиница: тутук белгиси приводится к одному знаку ---
    ("ma’no", "ma'no"),
    ("ma´no", "ma'no"),
    ("sur'at", "sur'at"),
    ("e'lon", "e'lon"),
    ("a'lo", "a'lo"),
    ("Is'hoq", "Is'hoq"),            # апостроф между s и h: не превращается в ş
    ("'salom'", "'salom'"),          # кавычки вокруг слова не трогаем
    # --- латиница: то, что меняться не должно ---
    ("kenglik", "kenglik"),
    ("bahor", "bahor"),
    # --- кириллица ---
    ("Ўзбекистон", "Özbekiston"),
    ("ғоя", "ğoya"),
    ("ШАҲАР", "ŞAHAR"),
    ("чой", "çoy"),
    ("Чой", "Çoy"),
    ("ЧОЙ", "ÇOY"),
    ("шахар", "şaxar"),
    ("Тошкент", "Toşkent"),
    ("ўқитувчи", "öqituvçi"),
    ("ШЎРО", "ŞÖRO"),
    ("ҳаво", "havo"),
    ("цирк", "sirk"),
    ("станция", "stansiya"),
    # --- кириллица: е, ё, ю, я ---
    ("Ёш", "Yoş"),
    ("ЁШ", "YOŞ"),
    ("ёш", "yoş"),
    ("Юлдуз", "Yulduz"),
    ("Яхши", "Yaxşi"),
    ("ЯХШИ", "YAXŞI"),
    ("Ева", "Yeva"),
    ("Эшик", "Eşik"),
    # --- кириллица: ъ и сҳ ---
    ("маъно", "ma'no"),
    ("аъло", "a'lo"),
    ("масъул", "mas'ul"),
    ("объект", "ob'yekt"),
    ("съезд", "s'yezd"),
    ("сҳ", "s'h"),
    # --- смесь и знаки препинания ---
    ("Toshkent — Тошкент", "Toşkent — Toşkent"),
    ("123 shahar, ЧОЙ! O'zbek?", "123 şahar, ÇOY! Özbek?"),
    ("Привет, мир", "Privet, mir"),
]


class TestConvert(unittest.TestCase):
    def test_cases(self):
        for source, expected in CASES:
            with self.subTest(source=source):
                self.assertEqual(convert(source), expected)

    def test_multiline(self):
        text = "O'zbek\nChoy\n\nШахар"
        self.assertEqual(convert(text), "Özbek\nÇoy\n\nŞaxar")

    def test_idempotent(self):
        # повторный прогон уже готового текста ничего не должен менять
        for source, _ in CASES:
            once = convert(source)
            self.assertEqual(convert(once), once, msg=source)


if __name__ == "__main__":
    unittest.main(verbosity=1)
