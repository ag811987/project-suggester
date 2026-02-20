"""Document parser service for extracting text from uploaded files.

Supports PDF, DOCX, and TXT file formats.
"""

import io

from pypdf import PdfReader
from docx import Document as DocxDocument


class DocumentParser:
    """Parses uploaded documents and extracts their text content."""

    SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".txt"}

    def parse_file(self, file: io.BytesIO, filename: str) -> str:
        """Parse a file based on its extension.

        Args:
            file: File-like object containing the document bytes.
            filename: Original filename (used to determine format).

        Returns:
            Extracted text content.

        Raises:
            ValueError: If the file format is unsupported.
        """
        ext = self._get_extension(filename)
        if ext == ".pdf":
            return self.parse_pdf(file)
        elif ext == ".docx":
            return self.parse_docx(file)
        elif ext == ".txt":
            return self.parse_txt(file)
        else:
            raise ValueError(f"Unsupported file format: {ext}")

    def parse_pdf(self, file: io.BytesIO) -> str:
        """Extract text from a PDF file.

        Args:
            file: File-like object containing PDF bytes.

        Returns:
            Concatenated text from all pages.

        Raises:
            ValueError: If the PDF cannot be parsed.
        """
        try:
            reader = PdfReader(file)
            pages_text = []
            for page in reader.pages:
                text = page.extract_text()
                if text:
                    pages_text.append(text)
            return "\n".join(pages_text)
        except Exception as e:
            raise ValueError(f"Failed to parse PDF: {e}") from e

    def parse_docx(self, file: io.BytesIO) -> str:
        """Extract text from a DOCX file.

        Args:
            file: File-like object containing DOCX bytes.

        Returns:
            Concatenated text from all paragraphs.

        Raises:
            ValueError: If the DOCX cannot be parsed.
        """
        try:
            doc = DocxDocument(file)
            paragraphs = [p.text for p in doc.paragraphs if p.text]
            return "\n".join(paragraphs)
        except Exception as e:
            raise ValueError(f"Failed to parse DOCX: {e}") from e

    def parse_txt(self, file: io.BytesIO) -> str:
        """Extract text from a plain text file.

        Args:
            file: File-like object containing text bytes.

        Returns:
            The decoded text content.
        """
        return file.read().decode("utf-8")

    def _get_extension(self, filename: str) -> str:
        """Get the lowercase file extension including the dot."""
        dot_idx = filename.rfind(".")
        if dot_idx == -1:
            return ""
        return filename[dot_idx:].lower()
