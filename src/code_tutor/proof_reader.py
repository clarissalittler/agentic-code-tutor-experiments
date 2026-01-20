"""Proof file reading and parsing utilities."""

import re
from pathlib import Path
from typing import Dict, List, Optional, Any


class ProofReader:
    """Handles reading and metadata extraction for proof files."""

    # Supported proof file formats
    SUPPORTED_EXTENSIONS = {
        # Plain text and markdown
        ".txt": "Plain Text",
        ".md": "Markdown",
        ".markdown": "Markdown",
        # LaTeX
        ".tex": "LaTeX",
        ".latex": "LaTeX",
        # Formal proof assistants
        ".lean": "Lean",
        ".lean4": "Lean 4",
        ".v": "Coq",
        ".agda": "Agda",
        ".thy": "Isabelle",
        ".idr": "Idris",
        # Other
        ".org": "Org Mode",
        ".rst": "reStructuredText",
    }

    # Mathematical domains for context
    MATH_DOMAINS = [
        "real analysis",
        "complex analysis",
        "linear algebra",
        "abstract algebra",
        "group theory",
        "ring theory",
        "topology",
        "algebraic topology",
        "differential geometry",
        "number theory",
        "combinatorics",
        "graph theory",
        "probability",
        "statistics",
        "logic",
        "set theory",
        "category theory",
        "measure theory",
        "functional analysis",
        "discrete mathematics",
        "computer science theory",
        "algorithms",
        "computability",
        "type theory",
    ]

    # Experience levels for proof review
    EXPERIENCE_LEVELS = [
        "student",       # Taking first proof-based course
        "undergrad",     # Undergraduate math major
        "graduate",      # Graduate student
        "researcher",    # Professional mathematician/researcher
    ]

    def __init__(self):
        """Initialize the proof reader."""
        pass

    def read_file(self, file_path: str) -> Dict[str, Any]:
        """Read a proof file and extract metadata.

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
            # Try UTF-8 first, fall back to latin-1
            try:
                with open(path, "r", encoding="utf-8") as f:
                    content = f.read()
                encoding = "utf-8"
            except UnicodeDecodeError:
                with open(path, "r", encoding="latin-1") as f:
                    content = f.read()
                encoding = "latin-1"

            metadata = self._extract_metadata(path, content, encoding)
            structure = self._analyze_proof_structure(content, metadata["format"])

            return {
                "path": str(path.absolute()),
                "name": path.name,
                "content": content,
                "metadata": metadata,
                "structure": structure,
            }

        except IOError as e:
            raise ValueError(f"Failed to read file: {e}")

    def _extract_metadata(self, path: Path, content: str, encoding: str) -> Dict[str, Any]:
        """Extract metadata from proof file.

        Args:
            path: File path.
            content: File content.
            encoding: Detected encoding.

        Returns:
            Metadata dictionary.
        """
        lines = content.split("\n")
        extension = path.suffix.lower()
        proof_format = self.SUPPORTED_EXTENSIONS.get(extension, "Unknown")

        # Detect if it's a formal proof
        is_formal = extension in [".lean", ".lean4", ".v", ".agda", ".thy", ".idr"]

        # Try to detect domain from content
        detected_domain = self._detect_domain(content)

        return {
            "format": proof_format,
            "extension": extension,
            "size_bytes": len(content.encode(encoding)),
            "line_count": len(lines),
            "encoding": encoding,
            "non_empty_lines": sum(1 for line in lines if line.strip()),
            "is_formal": is_formal,
            "detected_domain": detected_domain,
        }

    def _detect_domain(self, content: str) -> Optional[str]:
        """Try to detect the mathematical domain from content.

        Args:
            content: Proof content.

        Returns:
            Detected domain or None.
        """
        content_lower = content.lower()

        # Domain keywords
        domain_keywords = {
            "real analysis": ["continuous", "limit", "derivative", "integral", "epsilon", "delta", "convergence", "sequence", "series"],
            "linear algebra": ["matrix", "vector", "eigenvalue", "eigenvector", "linear transformation", "basis", "dimension", "kernel", "rank"],
            "abstract algebra": ["group", "ring", "field", "homomorphism", "isomorphism", "subgroup", "ideal", "quotient"],
            "topology": ["open set", "closed set", "compact", "connected", "homeomorphism", "neighborhood", "metric space"],
            "number theory": ["prime", "divisibility", "congruence", "modular", "diophantine", "gcd", "lcm"],
            "combinatorics": ["permutation", "combination", "binomial", "counting", "pigeonhole"],
            "graph theory": ["vertex", "edge", "path", "cycle", "tree", "degree", "adjacency"],
            "logic": ["implies", "forall", "exists", "and", "or", "not", "iff", "contradiction", "negation"],
            "set theory": ["subset", "union", "intersection", "cardinality", "bijection", "injection", "surjection"],
            "probability": ["probability", "random variable", "expected value", "variance", "distribution"],
            "type theory": ["type", "term", "judgment", "dependent type", "universe", "induction"],
        }

        # Count keyword matches for each domain
        scores = {}
        for domain, keywords in domain_keywords.items():
            score = sum(1 for kw in keywords if kw in content_lower)
            if score > 0:
                scores[domain] = score

        if scores:
            return max(scores, key=scores.get)

        return None

    def _analyze_proof_structure(self, content: str, proof_format: str) -> Dict[str, Any]:
        """Analyze the structure of the proof.

        Args:
            content: Proof content.
            proof_format: Format of the proof file.

        Returns:
            Structure analysis dictionary.
        """
        structure = {
            "has_theorem_statement": False,
            "has_proof_body": False,
            "proof_techniques": [],
            "lemmas_referenced": [],
            "definitions_used": [],
            "sections": [],
        }

        content_lower = content.lower()

        # Check for theorem/lemma/proposition statements
        statement_patterns = [
            r'\b(theorem|lemma|proposition|corollary|claim)\b',
        ]
        for pattern in statement_patterns:
            if re.search(pattern, content_lower):
                structure["has_theorem_statement"] = True
                break

        # Check for proof body
        proof_patterns = [
            r'\bproof\b',
            r'\bproof\.',
            r'\\begin\{proof\}',
            r'∎',
            r'q\.e\.d\.',
            r'qed',
        ]
        for pattern in proof_patterns:
            if re.search(pattern, content_lower):
                structure["has_proof_body"] = True
                break

        # Detect proof techniques
        techniques = {
            "induction": [r'\binduction\b', r'\binductive\b', r'\bbase case\b', r'\binductive step\b'],
            "contradiction": [r'\bcontradiction\b', r'\bsuppose.*not\b', r'\bassume.*false\b'],
            "contrapositive": [r'\bcontrapositive\b'],
            "direct": [r'\bdirect proof\b', r'\bdirectly\b'],
            "construction": [r'\bconstruct\b', r'\bdefine\b.*to be\b'],
            "cases": [r'\bcase\s+\d\b', r'\bby cases\b', r'\bcases?\s*:\s*\n'],
            "strong induction": [r'\bstrong induction\b'],
            "well-ordering": [r'\bwell-ordering\b', r'\bwell ordering\b'],
            "diagonalization": [r'\bdiagonalization\b', r'\bdiagonal argument\b'],
            "pigeonhole": [r'\bpigeonhole\b'],
        }

        for technique, patterns in techniques.items():
            for pattern in patterns:
                if re.search(pattern, content_lower):
                    if technique not in structure["proof_techniques"]:
                        structure["proof_techniques"].append(technique)
                    break

        # For LaTeX, try to find sections
        if proof_format == "LaTeX":
            section_matches = re.findall(r'\\(?:section|subsection|subsubsection)\{([^}]+)\}', content)
            structure["sections"] = section_matches

        # For Lean/Coq, find theorem names
        if proof_format in ["Lean", "Lean 4"]:
            theorem_matches = re.findall(r'(?:theorem|lemma)\s+(\w+)', content)
            structure["lemmas_referenced"] = theorem_matches
        elif proof_format == "Coq":
            theorem_matches = re.findall(r'(?:Theorem|Lemma|Proposition)\s+(\w+)', content)
            structure["lemmas_referenced"] = theorem_matches

        return structure

    def is_supported(self, file_path: str) -> bool:
        """Check if a file type is supported.

        Args:
            file_path: Path to check.

        Returns:
            True if supported, False otherwise.
        """
        extension = Path(file_path).suffix.lower()
        return extension in self.SUPPORTED_EXTENSIONS

    def get_format(self, file_path: str) -> Optional[str]:
        """Get the format for a file.

        Args:
            file_path: Path to check.

        Returns:
            Format name or None if not supported.
        """
        extension = Path(file_path).suffix.lower()
        return self.SUPPORTED_EXTENSIONS.get(extension)

    def validate_domain(self, domain: str) -> bool:
        """Validate a mathematical domain.

        Args:
            domain: Domain to validate.

        Returns:
            True if valid, False otherwise.
        """
        return domain.lower() in [d.lower() for d in self.MATH_DOMAINS]

    def validate_experience_level(self, level: str) -> bool:
        """Validate an experience level.

        Args:
            level: Level to validate.

        Returns:
            True if valid, False otherwise.
        """
        return level.lower() in [l.lower() for l in self.EXPERIENCE_LEVELS]
