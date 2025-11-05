"""File reading and parsing utilities."""

import os
from pathlib import Path
from typing import Dict, List, Optional


class FileReader:
    """Handles reading and metadata extraction for source code files."""

    # Common source code file extensions
    SUPPORTED_EXTENSIONS = {
        ".py": "Python",
        ".js": "JavaScript",
        ".ts": "TypeScript",
        ".jsx": "JavaScript (React)",
        ".tsx": "TypeScript (React)",
        ".java": "Java",
        ".c": "C",
        ".cpp": "C++",
        ".cc": "C++",
        ".h": "C/C++ Header",
        ".hpp": "C++ Header",
        ".cs": "C#",
        ".go": "Go",
        ".rs": "Rust",
        ".rb": "Ruby",
        ".php": "PHP",
        ".swift": "Swift",
        ".kt": "Kotlin",
        ".scala": "Scala",
        ".sh": "Shell Script",
        ".bash": "Bash Script",
        ".sql": "SQL",
        ".html": "HTML",
        ".css": "CSS",
        ".scss": "SCSS",
        ".sass": "Sass",
        ".json": "JSON",
        ".yaml": "YAML",
        ".yml": "YAML",
        ".xml": "XML",
        ".md": "Markdown",
        ".r": "R",
        ".R": "R",
    }

    def __init__(self):
        """Initialize the file reader."""
        pass

    def read_file(self, file_path: str) -> Dict[str, any]:
        """Read a source code file and extract metadata.

        Args:
            file_path: Path to the file to read.

        Returns:
            Dictionary containing file content and metadata.

        Raises:
            FileNotFoundError: If file doesn't exist.
            ValueError: If file type is not supported.
        """
        path = Path(file_path)

        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        if not path.is_file():
            raise ValueError(f"Path is not a file: {file_path}")

        extension = path.suffix.lower()
        if extension not in self.SUPPORTED_EXTENSIONS:
            raise ValueError(
                f"Unsupported file type: {extension}. "
                f"Supported types: {', '.join(self.SUPPORTED_EXTENSIONS.keys())}"
            )

        try:
            # Try UTF-8 first, fall back to latin-1 if that fails
            try:
                with open(path, "r", encoding="utf-8") as f:
                    content = f.read()
                encoding = "utf-8"
            except UnicodeDecodeError:
                with open(path, "r", encoding="latin-1") as f:
                    content = f.read()
                encoding = "latin-1"

            metadata = self._extract_metadata(path, content, encoding)

            return {
                "path": str(path.absolute()),
                "name": path.name,
                "content": content,
                "metadata": metadata,
            }

        except IOError as e:
            raise ValueError(f"Failed to read file: {e}")

    def _extract_metadata(self, path: Path, content: str, encoding: str) -> Dict[str, any]:
        """Extract metadata from file.

        Args:
            path: File path.
            content: File content.
            encoding: Detected encoding.

        Returns:
            Metadata dictionary.
        """
        lines = content.split("\n")
        extension = path.suffix.lower()

        return {
            "language": self.SUPPORTED_EXTENSIONS.get(extension, "Unknown"),
            "extension": extension,
            "size_bytes": len(content.encode(encoding)),
            "line_count": len(lines),
            "encoding": encoding,
            "non_empty_lines": sum(1 for line in lines if line.strip()),
        }

    def is_supported(self, file_path: str) -> bool:
        """Check if a file type is supported.

        Args:
            file_path: Path to check.

        Returns:
            True if supported, False otherwise.
        """
        extension = Path(file_path).suffix.lower()
        return extension in self.SUPPORTED_EXTENSIONS

    def get_language(self, file_path: str) -> Optional[str]:
        """Get the language for a file.

        Args:
            file_path: Path to check.

        Returns:
            Language name or None if not supported.
        """
        extension = Path(file_path).suffix.lower()
        return self.SUPPORTED_EXTENSIONS.get(extension)

    def find_files(self, directory: str, recursive: bool = True) -> List[str]:
        """Find all supported source files in a directory.

        Args:
            directory: Directory path to search.
            recursive: Whether to search recursively.

        Returns:
            List of file paths.

        Raises:
            NotADirectoryError: If path is not a directory.
        """
        dir_path = Path(directory)

        if not dir_path.exists():
            raise FileNotFoundError(f"Directory not found: {directory}")

        if not dir_path.is_dir():
            raise NotADirectoryError(f"Path is not a directory: {directory}")

        files = []

        if recursive:
            for root, _, filenames in os.walk(dir_path):
                for filename in filenames:
                    file_path = Path(root) / filename
                    if self.is_supported(str(file_path)):
                        files.append(str(file_path))
        else:
            for item in dir_path.iterdir():
                if item.is_file() and self.is_supported(str(item)):
                    files.append(str(item))

        return sorted(files)
