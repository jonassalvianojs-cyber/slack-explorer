import os
import stat
import tempfile
import unittest
from pathlib import Path

from slack_explorer.core import human_size, list_directory, permission_text


class CoreTests(unittest.TestCase):
    def test_human_size(self):
        self.assertEqual(human_size(0), "0 B")
        self.assertEqual(human_size(1536), "1.5 KB")
        self.assertEqual(human_size(20, is_dir=True), "")

    def test_listing_hides_dotfiles_and_sorts_folders_first(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "zeta.txt").write_text("teste", encoding="utf-8")
            (root / ".oculto").write_text("segredo", encoding="utf-8")
            (root / "Pasta").mkdir()
            entries = list_directory(root)
            self.assertEqual([item.name for item in entries], ["Pasta", "zeta.txt"])
            self.assertEqual(len(list_directory(root, show_hidden=True)), 3)

    def test_case_insensitive_filter(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "Relatorio.PDF").touch()
            (root / "foto.png").touch()
            self.assertEqual([item.name for item in list_directory(root, query="pdf")], ["Relatorio.PDF"])

    def test_permission_text(self):
        mode = stat.S_IFREG | stat.S_IRUSR | stat.S_IWUSR
        self.assertEqual(permission_text(mode), "-rw-------")


if __name__ == "__main__":
    unittest.main()
