"""
File reading and parsing utilities.

📚 FILE OVERVIEW:
This file handles reading source code files, detecting their language/type,
extracting metadata (like line count and size), and finding files in directories.
It's a utility class that abstracts file I/O complexity.

🎯 WHAT YOU'LL LEARN:
- File extension mapping for language detection
- Encoding detection and fallback strategies
- Metadata extraction from files
- Recursive directory traversal
- Error handling for file operations
- Using pathlib for file operations

💡 WHY THIS FILE EXISTS:
When analyzing code, we need to:
1. Read files safely (handle encoding issues)
2. Know what language the code is in
3. Get metadata (size, lines) for context
4. Find all code files in a directory
This class provides all of that in a clean API.
"""

# ============================================================================
# IMPORTS
# ============================================================================

import os  # 🔍 Used for os.walk() to traverse directories recursively
from pathlib import Path  # 🎯 Modern, object-oriented file path handling
from typing import Dict, List, Optional  # 💡 Type hints for documentation


# ============================================================================
# FileReader CLASS
# ============================================================================

class FileReader:
    """
    Handles reading and metadata extraction for source code files.

    🔍 DESIGN: Utility/Helper Class
    This is a stateless utility class - all methods could be static, but
    keeping them as instance methods allows for future extension (e.g.,
    adding custom file type mappings per instance).

    💡 KEY RESPONSIBILITIES:
    1. Determine file types by extension
    2. Read files with proper encoding handling
    3. Extract metadata (language, lines, size)
    4. Find supported files in directories
    """

    # ------------------------------------------------------------------------
    # CLASS CONSTANTS: FILE TYPE MAPPINGS
    # ------------------------------------------------------------------------
    # 🔍 This dictionary maps file extensions to language names

    SUPPORTED_EXTENSIONS = {
        # Python
        ".py": "Python",

        # JavaScript/TypeScript
        ".js": "JavaScript",
        ".ts": "TypeScript",
        ".jsx": "JavaScript (React)",  # 💡 React components
        ".tsx": "TypeScript (React)",

        # Java
        ".java": "Java",

        # C/C++
        ".c": "C",
        ".cpp": "C++",
        ".cc": "C++",  # 🔍 Alternative C++ extension
        ".h": "C/C++ Header",
        ".hpp": "C++ Header",

        # Other compiled languages
        ".cs": "C#",
        ".go": "Go",
        ".rs": "Rust",

        # Scripting languages
        ".rb": "Ruby",
        ".php": "PHP",
        ".swift": "Swift",

        # JVM languages
        ".kt": "Kotlin",
        ".scala": "Scala",

        # Shell scripting
        ".sh": "Shell Script",
        ".bash": "Bash Script",

        # Data/Query
        ".sql": "SQL",

        # Web
        ".html": "HTML",
        ".css": "CSS",
        ".scss": "SCSS",  # 💡 Sass preprocessor
        ".sass": "Sass",

        # Configuration/Data
        ".json": "JSON",
        ".yaml": "YAML",
        ".yml": "YAML",  # 🔍 Alternative YAML extension
        ".xml": "XML",

        # Documentation
        ".md": "Markdown",

        # Statistical
        ".r": "R",
        ".R": "R",  # ⚠️ R extensions are case-sensitive!
    }
    # 🎯 Total: 25+ supported file types!

    # ------------------------------------------------------------------------
    # INITIALIZATION
    # ------------------------------------------------------------------------

    def __init__(self):
        """
        Initialize the file reader.

        💡 Currently does nothing (pass), but we include it for:
        1. Consistency (all classes have __init__)
        2. Future extension (might add instance variables later)
        3. Documentation (can add docstring)
        """
        pass

    # ------------------------------------------------------------------------
    # MAIN FILE READING METHOD
    # ------------------------------------------------------------------------

    def read_file(self, file_path: str) -> Dict[str, any]:
        """
        Read a source code file and extract metadata.

        🔍 THIS IS THE MAIN METHOD - everything else supports this!

        💡 WHAT IT DOES:
        1. Validates the file exists and is readable
        2. Checks if file type is supported
        3. Reads content with encoding detection
        4. Extracts metadata (language, lines, size, etc.)
        5. Returns everything in a structured dictionary

        Args:
            file_path: Path to the file to read.

        Returns:
            Dictionary containing:
            {
                "path": "/absolute/path/to/file.py",
                "name": "file.py",
                "content": "file contents as string",
                "metadata": {
                    "language": "Python",
                    "extension": ".py",
                    "size_bytes": 1234,
                    "line_count": 50,
                    "encoding": "utf-8",
                    "non_empty_lines": 42
                }
            }

        Raises:
            FileNotFoundError: If file doesn't exist.
            ValueError: If file type is not supported.

        🎯 USAGE EXAMPLE:
            >>> reader = FileReader()
            >>> data = reader.read_file("example.py")
            >>> print(data["metadata"]["language"])  # "Python"
            >>> print(data["content"])  # The actual code
        """
        # Convert string path to Path object for easier manipulation
        # 🔍 pathlib makes path operations object-oriented and cross-platform
        path = Path(file_path)

        # ------------------------
        # VALIDATION STEP 1: File exists?
        # ------------------------
        if not path.exists():
            # ⚠️ Specific error type helps calling code handle this case
            raise FileNotFoundError(f"File not found: {file_path}")

        # ------------------------
        # VALIDATION STEP 2: Is it a file (not a directory)?
        # ------------------------
        if not path.is_file():
            raise ValueError(f"Path is not a file: {file_path}")

        # ------------------------
        # VALIDATION STEP 3: Is the file type supported?
        # ------------------------
        # Get extension and normalize to lowercase
        # 🔍 .suffix gets extension like ".py", .lower() handles ".PY"
        extension = path.suffix.lower()

        if extension not in self.SUPPORTED_EXTENSIONS:
            # Build helpful error message listing supported types
            raise ValueError(
                f"Unsupported file type: {extension}. "
                f"Supported types: {', '.join(self.SUPPORTED_EXTENSIONS.keys())}"
            )

        # ------------------------
        # READING WITH ENCODING DETECTION
        # ------------------------
        try:
            # 🔍 KEY PATTERN: Try UTF-8, fall back to Latin-1
            # Most source code is UTF-8, but some older files use Latin-1

            # Try UTF-8 first (most common)
            try:
                with open(path, "r", encoding="utf-8") as f:
                    content = f.read()
                encoding = "utf-8"

            except UnicodeDecodeError:
                # 💡 If UTF-8 fails, try Latin-1 (ISO-8859-1)
                # Latin-1 accepts all byte values, so it won't fail
                # ⚠️ This is a safe fallback but might not be correct encoding
                with open(path, "r", encoding="latin-1") as f:
                    content = f.read()
                encoding = "latin-1"

            # Extract metadata about the file
            metadata = self._extract_metadata(path, content, encoding)

            # Return structured data
            # 🎯 Consistent return format makes this easy to use
            return {
                "path": str(path.absolute()),  # Absolute path as string
                "name": path.name,  # Just filename, e.g., "file.py"
                "content": content,  # The actual file contents
                "metadata": metadata,  # Detailed metadata
            }

        except IOError as e:
            # 💡 IOError covers many file-related issues:
            # - Permission denied
            # - Disk I/O error
            # - File in use by another program
            raise ValueError(f"Failed to read file: {e}")

    # ------------------------------------------------------------------------
    # METADATA EXTRACTION
    # ------------------------------------------------------------------------

    def _extract_metadata(self, path: Path, content: str, encoding: str) -> Dict[str, any]:
        """
        Extract metadata from file.

        🔍 PRIVATE METHOD (starts with _)
        This is an internal helper, not meant to be called directly.

        💡 WHAT IT CALCULATES:
        - Language (from extension)
        - File size in bytes
        - Total lines
        - Non-empty lines (excludes blank lines)
        - Encoding used

        Args:
            path: File path.
            content: File content.
            encoding: Detected encoding.

        Returns:
            Metadata dictionary.
        """
        # Split content into lines
        # 🔍 "\n" is the newline character - split on it to count lines
        lines = content.split("\n")

        # Get file extension (normalized to lowercase)
        extension = path.suffix.lower()

        # Build and return metadata dictionary
        return {
            # Look up language name from extension
            # 💡 .get() with default handles unknown extensions gracefully
            "language": self.SUPPORTED_EXTENSIONS.get(extension, "Unknown"),

            # The extension itself (e.g., ".py")
            "extension": extension,

            # Calculate size in bytes
            # 🔍 Must encode to bytes to get accurate size
            # Different encodings use different bytes per character
            "size_bytes": len(content.encode(encoding)),

            # Total number of lines
            "line_count": len(lines),

            # Which encoding was used
            "encoding": encoding,

            # Count non-empty lines (excludes blank lines)
            # 🎯 line.strip() removes whitespace; if result is non-empty, count it
            # sum(1 for ...) is a Python idiom for counting
            "non_empty_lines": sum(1 for line in lines if line.strip()),
        }

    # ------------------------------------------------------------------------
    # HELPER METHODS
    # ------------------------------------------------------------------------

    def is_supported(self, file_path: str) -> bool:
        """
        Check if a file type is supported.

        💡 USE CASE: Before trying to read a file, check if we support it.
        This is faster than trying to read and catching an error.

        Args:
            file_path: Path to check.

        Returns:
            True if supported, False otherwise.

        🎯 EXAMPLE:
            >>> reader = FileReader()
            >>> reader.is_supported("test.py")  # True
            >>> reader.is_supported("test.pdf")  # False
        """
        # Get extension in lowercase
        extension = Path(file_path).suffix.lower()
        # Check if in our supported set
        return extension in self.SUPPORTED_EXTENSIONS

    def get_language(self, file_path: str) -> Optional[str]:
        """
        Get the language for a file.

        💡 Similar to is_supported(), but returns the actual language name
        instead of just True/False.

        Args:
            file_path: Path to check.

        Returns:
            Language name or None if not supported.

        🎯 EXAMPLE:
            >>> reader.get_language("test.py")  # "Python"
            >>> reader.get_language("test.pdf")  # None
        """
        extension = Path(file_path).suffix.lower()
        # 🔍 .get() returns None by default if key not found
        return self.SUPPORTED_EXTENSIONS.get(extension)

    # ------------------------------------------------------------------------
    # DIRECTORY TRAVERSAL
    # ------------------------------------------------------------------------

    def find_files(self, directory: str, recursive: bool = True) -> List[str]:
        """
        Find all supported source files in a directory.

        🔍 KEY FEATURE: Recursive vs. Non-recursive search
        - Recursive: Search all subdirectories (like find or tree)
        - Non-recursive: Only top-level files (like ls)

        💡 TWO DIFFERENT APPROACHES:
        - Recursive uses os.walk() - standard Python approach
        - Non-recursive uses pathlib iteration - more modern

        Args:
            directory: Directory path to search.
            recursive: Whether to search recursively (default: True).

        Returns:
            List of file paths (sorted alphabetically).

        Raises:
            NotADirectoryError: If path is not a directory.

        🎯 USAGE:
            >>> reader = FileReader()
            >>> files = reader.find_files("src/", recursive=True)
            >>> print(files)  # ['src/main.py', 'src/utils/helper.py', ...]
        """
        # Convert to Path object
        dir_path = Path(directory)

        # ------------------------
        # VALIDATION
        # ------------------------
        if not dir_path.exists():
            raise FileNotFoundError(f"Directory not found: {directory}")

        if not dir_path.is_dir():
            # ⚠️ Specific exception type for clarity
            raise NotADirectoryError(f"Path is not a directory: {directory}")

        # Initialize results list
        files = []

        # ------------------------
        # RECURSIVE SEARCH
        # ------------------------
        if recursive:
            # 🔍 os.walk() is the classic Python way to traverse directories
            # It yields (current_dir, subdirs, files) for each directory

            for root, _, filenames in os.walk(dir_path):
                # root: Current directory being visited
                # _: List of subdirectories (we don't need it, so use _)
                # filenames: List of files in current directory

                for filename in filenames:
                    # Build full path
                    file_path = Path(root) / filename

                    # Check if it's a supported type
                    if self.is_supported(str(file_path)):
                        files.append(str(file_path))

        # ------------------------
        # NON-RECURSIVE SEARCH
        # ------------------------
        else:
            # 🎯 pathlib's iterdir() is cleaner for non-recursive
            # It returns an iterator of all items in the directory

            for item in dir_path.iterdir():
                # Check if it's a file (not a subdirectory)
                if item.is_file() and self.is_supported(str(item)):
                    files.append(str(item))

        # Return sorted list (alphabetical order)
        # 💡 Sorting makes output predictable and easier to work with
        return sorted(files)


# ============================================================================
# KEY TAKEAWAYS
# ============================================================================
"""
🎓 WHAT YOU LEARNED:

1. **File Type Detection**
   - Map extensions to languages with a dictionary
   - Normalize extensions to lowercase (.PY → .py)
   - Use descriptive language names

2. **Encoding Handling**
   - Try UTF-8 first (most common for source code)
   - Fall back to Latin-1 if UTF-8 fails
   - Track which encoding was used

3. **Metadata Extraction**
   - Split by newline to count lines
   - Use .strip() to identify non-empty lines
   - Calculate byte size by encoding content

4. **Path Handling**
   - Use pathlib.Path instead of string manipulation
   - .exists(), .is_file(), .is_dir() for validation
   - .suffix for extension, .name for filename

5. **Directory Traversal**
   - os.walk() for recursive (traditional approach)
   - .iterdir() for non-recursive (modern approach)
   - Always sort results for predictability

6. **Error Handling**
   - Specific exceptions (FileNotFoundError, ValueError, IOError)
   - Helpful error messages with context
   - Handle UnicodeDecodeError gracefully

7. **Return Value Design**
   - Structured dictionaries with consistent keys
   - Separate "data" from "metadata"
   - Document return format in docstrings

🔧 COMMON PATTERNS:

**Pattern: Try/Except with Fallback**
```python
try:
    # Try preferred approach
    result = preferred_method()
except SpecificError:
    # Fall back to alternative
    result = fallback_method()
```

**Pattern: Validation Before Processing**
```python
if not valid:
    raise SpecificError("Clear message")
# Process only if valid
```

**Pattern: Building Lists with Filtering**
```python
results = []
for item in items:
    if meets_criteria(item):
        results.append(item)
return sorted(results)
```

📚 FURTHER LEARNING:
- Python's pathlib module documentation
- Character encodings (UTF-8, Latin-1, etc.)
- os.walk() vs. Path.iterdir() vs. Path.glob()
- File I/O best practices
- Cross-platform path handling
