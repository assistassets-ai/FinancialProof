"""
Tests fuer das Uebersetzungsmodul (TranslationSystem).
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from translator import TranslationSystem


class TestIsGerman:
    def _ts(self, tmp_path):
        return TranslationSystem(app_dir=tmp_path)

    def test_detects_umlaut_ae(self, tmp_path):
        ts = self._ts(tmp_path)
        assert ts._is_german("Überprüfung")

    def test_detects_umlaut_oe(self, tmp_path):
        ts = self._ts(tmp_path)
        assert ts._is_german("Größe")

    def test_detects_umlaut_ue(self, tmp_path):
        ts = self._ts(tmp_path)
        assert ts._is_german("Schüler")

    def test_detects_eszett(self, tmp_path):
        ts = self._ts(tmp_path)
        assert ts._is_german("Straße")

    def test_detects_uppercase_umlaut(self, tmp_path):
        ts = self._ts(tmp_path)
        assert ts._is_german("Öffnen")

    def test_plain_english_not_german(self, tmp_path):
        """Englische Wörter ohne Umlaute und ohne deutsche Hinweiswörter sind NICHT deutsch."""
        ts = self._ts(tmp_path)
        assert not ts._is_german("Hello World")

    def test_ascii_only_latin_not_german(self, tmp_path):
        """ASCII-Buchstaben a,e,o,u,s (alte kaputte Prüfung) dürfen NICHT ausreichen."""
        ts = self._ts(tmp_path)
        assert not ts._is_german("source")

    def test_german_hint_word_detected(self, tmp_path):
        """Bekannte deutsche Hinweiswörter werden als deutsch erkannt."""
        ts = self._ts(tmp_path)
        assert ts._is_german("datei laden")

    def test_empty_string_not_german(self, tmp_path):
        ts = self._ts(tmp_path)
        assert not ts._is_german("")
