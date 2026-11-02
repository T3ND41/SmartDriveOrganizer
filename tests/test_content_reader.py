from __future__ import annotations

import tempfile
import unittest
import zipfile
import sys
from types import ModuleType, SimpleNamespace
from unittest.mock import patch
from pathlib import Path

from smart_drive_organizer.content_reader import MAX_TEXT_CHARS, read_document_text, _validate_office_archive


class ContentReaderTests(unittest.TestCase):
    def test_plain_text_extraction_is_not_limited_to_old_twelve_thousand_character_window(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "long.txt"
            content = "supplier quotation pressure valve " * 1000
            path.write_text(content, encoding="utf-8")
            result = read_document_text(path)
            self.assertGreater(len(result), 12000)
            self.assertLessEqual(len(result), MAX_TEXT_CHARS)


    def test_office_archive_total_uncompressed_limit_is_enforced(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "oversized.docx"
            with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
                archive.writestr("word/document.xml", "<root>content</root>")
            with patch("smart_drive_organizer.content_reader.MAX_ARCHIVE_TOTAL_BYTES", 4):
                with self.assertRaisesRegex(ValueError, "total extraction limit"):
                    _validate_office_archive(path)

    def test_office_archive_member_count_limit_is_enforced(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "many.docx"
            with zipfile.ZipFile(path, "w") as archive:
                archive.writestr("word/document.xml", "<root/>")
                archive.writestr("word/header1.xml", "<root/>")
            with patch("smart_drive_organizer.content_reader.MAX_ARCHIVE_ENTRIES", 1):
                with self.assertRaisesRegex(ValueError, "too many entries"):
                    _validate_office_archive(path)

    def test_docx_rejects_unsafe_archive_member_paths(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "unsafe.docx"
            with zipfile.ZipFile(path, "w") as archive:
                archive.writestr("../outside.xml", "<root/>")
            with self.assertRaisesRegex(ValueError, "unsafe member path"):
                _validate_office_archive(path)

    def test_eml_extracts_subject_sender_and_text_body(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "supplier.eml"
            path.write_text(
                "From: sales@example.test\nTo: buyer@example.test\nSubject: HDPE quotation\n"
                "Content-Type: text/plain; charset=utf-8\n\n"
                "Please find the pressure test certificate and supplier quotation attached.",
                encoding="utf-8",
            )
            text = read_document_text(path)
            self.assertIn("HDPE quotation", text)
            self.assertIn("sales@example.test", text)
            self.assertIn("pressure test certificate", text)

    def test_unsupported_or_corrupt_document_does_not_raise(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "bad.pdf"
            path.write_bytes(b"not a real PDF")
            self.assertEqual(read_document_text(path), "")


    def test_legacy_word_file_routes_to_optional_windows_reader(self):
        from unittest.mock import patch
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "legacy.doc"
            path.write_bytes(b"legacy Word placeholder")
            with patch("smart_drive_organizer.content_reader._legacy_office_text", return_value="legacy Word text") as reader:
                self.assertEqual(read_document_text(path), "legacy Word text")
                reader.assert_called_once_with(path, "word")

    def test_legacy_excel_file_routes_to_optional_windows_reader(self):
        from unittest.mock import patch
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "legacy.xls"
            path.write_bytes(b"legacy Excel placeholder")
            with patch("smart_drive_organizer.content_reader._legacy_office_text", return_value="legacy Excel text") as reader:
                self.assertEqual(read_document_text(path), "legacy Excel text")
                reader.assert_called_once_with(path, "excel")


    def test_legacy_powerpoint_reader_disables_macros_before_open(self):
        document = SimpleNamespace(Slides=SimpleNamespace(Count=0), Close=lambda: None)
        application = SimpleNamespace(
            Visible=None,
            DisplayAlerts=None,
            AutomationSecurity=None,
            Presentations=None,
            Quit=lambda: None,
        )
        def open_presentation(*args, **kwargs):
            self.assertEqual(application.AutomationSecurity, 3)
            self.assertFalse(application.Visible)
            self.assertEqual(application.DisplayAlerts, 0)
            return document
        application.Presentations = SimpleNamespace(Open=open_presentation)
        pythoncom = ModuleType("pythoncom")
        pythoncom.CoInitialize = lambda: None
        pythoncom.CoUninitialize = lambda: None
        win32com = ModuleType("win32com")
        client = ModuleType("win32com.client")
        client.DispatchEx = lambda _name: application
        win32com.client = client
        with patch.object(sys, "platform", "win32"), patch.dict(
            sys.modules, {"pythoncom": pythoncom, "win32com": win32com, "win32com.client": client}
        ):
            from smart_drive_organizer.content_reader import _legacy_office_text
            self.assertEqual(_legacy_office_text(Path("legacy.ppt"), "powerpoint"), "")

    def test_legacy_powerpoint_file_routes_to_optional_windows_reader(self):
        from unittest.mock import patch
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "legacy.ppt"
            path.write_bytes(b"legacy PowerPoint placeholder")
            with patch("smart_drive_organizer.content_reader._legacy_office_text", return_value="legacy PowerPoint text") as reader:
                self.assertEqual(read_document_text(path), "legacy PowerPoint text")
                reader.assert_called_once_with(path, "powerpoint")


if __name__ == "__main__":
    unittest.main()
