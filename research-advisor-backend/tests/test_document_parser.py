"""Tests for the document parser service."""

import io
from unittest.mock import MagicMock, patch

import pytest

from app.services.document_parser import DocumentParser


class TestDocumentParser:
    """Test suite for DocumentParser."""

    def setup_method(self):
        self.parser = DocumentParser()

    # --- TXT Parsing ---

    def test_parse_txt_returns_content(self):
        """TXT parsing should return the file content as a string."""
        content = b"This is a research proposal about quantum computing."
        result = self.parser.parse_txt(io.BytesIO(content))
        assert result == "This is a research proposal about quantum computing."

    def test_parse_txt_multiline(self):
        """TXT parsing should preserve multiline content."""
        content = b"Line one\nLine two\nLine three"
        result = self.parser.parse_txt(io.BytesIO(content))
        assert "Line one" in result
        assert "Line two" in result
        assert "Line three" in result

    def test_parse_txt_utf8(self):
        """TXT parsing should handle UTF-8 encoded text."""
        content = "Research on café culture and naïve approaches".encode("utf-8")
        result = self.parser.parse_txt(io.BytesIO(content))
        assert "café" in result
        assert "naïve" in result

    def test_parse_txt_empty_file(self):
        """TXT parsing of an empty file should return empty string."""
        result = self.parser.parse_txt(io.BytesIO(b""))
        assert result == ""

    # --- PDF Parsing ---

    @patch("app.services.document_parser.PdfReader")
    def test_parse_pdf_single_page(self, mock_pdf_reader_cls):
        """PDF parsing should extract text from a single-page PDF."""
        mock_page = MagicMock()
        mock_page.extract_text.return_value = "Quantum computing research paper."
        mock_reader = MagicMock()
        mock_reader.pages = [mock_page]
        mock_pdf_reader_cls.return_value = mock_reader

        result = self.parser.parse_pdf(io.BytesIO(b"fake pdf bytes"))
        assert result == "Quantum computing research paper."

    @patch("app.services.document_parser.PdfReader")
    def test_parse_pdf_multiple_pages(self, mock_pdf_reader_cls):
        """PDF parsing should concatenate text from multiple pages."""
        page1 = MagicMock()
        page1.extract_text.return_value = "Page one content."
        page2 = MagicMock()
        page2.extract_text.return_value = "Page two content."
        mock_reader = MagicMock()
        mock_reader.pages = [page1, page2]
        mock_pdf_reader_cls.return_value = mock_reader

        result = self.parser.parse_pdf(io.BytesIO(b"fake pdf bytes"))
        assert "Page one content." in result
        assert "Page two content." in result

    @patch("app.services.document_parser.PdfReader")
    def test_parse_pdf_empty_pages(self, mock_pdf_reader_cls):
        """PDF parsing should handle pages that return None for text."""
        mock_page = MagicMock()
        mock_page.extract_text.return_value = None
        mock_reader = MagicMock()
        mock_reader.pages = [mock_page]
        mock_pdf_reader_cls.return_value = mock_reader

        result = self.parser.parse_pdf(io.BytesIO(b"fake pdf bytes"))
        assert result == ""

    @patch("app.services.document_parser.PdfReader")
    def test_parse_pdf_error_handling(self, mock_pdf_reader_cls):
        """PDF parsing should raise ValueError on corrupt files."""
        mock_pdf_reader_cls.side_effect = Exception("Invalid PDF")

        with pytest.raises(ValueError, match="Failed to parse PDF"):
            self.parser.parse_pdf(io.BytesIO(b"not a pdf"))

    # --- DOCX Parsing ---

    @patch("app.services.document_parser.DocxDocument")
    def test_parse_docx_extracts_paragraphs(self, mock_docx_cls):
        """DOCX parsing should extract text from all paragraphs."""
        para1 = MagicMock()
        para1.text = "First paragraph about research."
        para2 = MagicMock()
        para2.text = "Second paragraph with methods."
        mock_doc = MagicMock()
        mock_doc.paragraphs = [para1, para2]
        mock_docx_cls.return_value = mock_doc

        result = self.parser.parse_docx(io.BytesIO(b"fake docx bytes"))
        assert "First paragraph about research." in result
        assert "Second paragraph with methods." in result

    @patch("app.services.document_parser.DocxDocument")
    def test_parse_docx_empty_document(self, mock_docx_cls):
        """DOCX parsing should handle documents with no paragraphs."""
        mock_doc = MagicMock()
        mock_doc.paragraphs = []
        mock_docx_cls.return_value = mock_doc

        result = self.parser.parse_docx(io.BytesIO(b"fake docx bytes"))
        assert result == ""

    @patch("app.services.document_parser.DocxDocument")
    def test_parse_docx_skips_empty_paragraphs(self, mock_docx_cls):
        """DOCX parsing should skip empty paragraphs."""
        para1 = MagicMock()
        para1.text = "Content paragraph."
        para2 = MagicMock()
        para2.text = ""
        para3 = MagicMock()
        para3.text = "Another content paragraph."
        mock_doc = MagicMock()
        mock_doc.paragraphs = [para1, para2, para3]
        mock_docx_cls.return_value = mock_doc

        result = self.parser.parse_docx(io.BytesIO(b"fake docx bytes"))
        assert "Content paragraph." in result
        assert "Another content paragraph." in result

    @patch("app.services.document_parser.DocxDocument")
    def test_parse_docx_error_handling(self, mock_docx_cls):
        """DOCX parsing should raise ValueError on corrupt files."""
        mock_docx_cls.side_effect = Exception("Invalid DOCX")

        with pytest.raises(ValueError, match="Failed to parse DOCX"):
            self.parser.parse_docx(io.BytesIO(b"not a docx"))

    # --- Generic parse method ---

    def test_parse_file_routes_txt(self):
        """parse_file should route .txt files to parse_txt."""
        content = b"Hello from txt"
        result = self.parser.parse_file(io.BytesIO(content), "notes.txt")
        assert result == "Hello from txt"

    @patch("app.services.document_parser.PdfReader")
    def test_parse_file_routes_pdf(self, mock_pdf_reader_cls):
        """parse_file should route .pdf files to parse_pdf."""
        mock_page = MagicMock()
        mock_page.extract_text.return_value = "PDF content"
        mock_reader = MagicMock()
        mock_reader.pages = [mock_page]
        mock_pdf_reader_cls.return_value = mock_reader

        result = self.parser.parse_file(io.BytesIO(b"fake"), "paper.pdf")
        assert result == "PDF content"

    @patch("app.services.document_parser.DocxDocument")
    def test_parse_file_routes_docx(self, mock_docx_cls):
        """parse_file should route .docx files to parse_docx."""
        para = MagicMock()
        para.text = "DOCX content"
        mock_doc = MagicMock()
        mock_doc.paragraphs = [para]
        mock_docx_cls.return_value = mock_doc

        result = self.parser.parse_file(io.BytesIO(b"fake"), "paper.docx")
        assert result == "DOCX content"

    def test_parse_file_unsupported_format(self):
        """parse_file should raise ValueError for unsupported formats."""
        with pytest.raises(ValueError, match="Unsupported file format"):
            self.parser.parse_file(io.BytesIO(b"data"), "image.png")

    def test_parse_file_case_insensitive_extension(self):
        """parse_file should handle uppercase extensions."""
        content = b"Hello from TXT"
        result = self.parser.parse_file(io.BytesIO(content), "NOTES.TXT")
        assert result == "Hello from TXT"
