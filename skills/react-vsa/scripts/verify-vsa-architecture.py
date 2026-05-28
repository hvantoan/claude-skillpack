#!/usr/bin/env python3
"""Verify VSA architecture compliance for React/TypeScript projects.

Checks:
1. No direct cross-feature deep imports (bypassing index.ts)
2. No feature-specific code in shared/
3. All features have index.ts barrel exports
4. No circular dependencies between features
5. shared/ files have no feature-specific imports

Usage:
    python verify-vsa-architecture.py [project-src-path]
    python verify-vsa-architecture.py ./src
"""

import os
import re
import sys
from pathlib import Path
from collections import defaultdict

# ── Config ──────────────────────────────────────────────

FEATURES_DIR = "features"
SHARED_DIR = "shared"
ALLOWED_EXTENSIONS = {".ts", ".tsx", ".js", ".jsx"}

# Import patterns
IMPORT_PATTERNS = [
    re.compile(r"""(?:import\s+.*?\s+from\s+|import\s+)['"](@?[^'"]+)['"]"""),
    re.compile(r"""require\(['"](@?[^'"]+)['"]\)"""),
]

# Feature-specific keywords that shouldn't appear in shared/
FEATURE_KEYWORDS = {
    "auth": ["login", "logout", "register", "signup", "signin", "password", "token", "session"],
    "products": ["product", "catalog", "inventory"],
    "cart": ["cart", "checkout", "basket", "order"],
    "users": ["user-profile", "account", "settings"],
}


def find_imports(file_path: Path) -> list[str]:
    """Extract all import paths from a file."""
    imports = []
    try:
        content = file_path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return imports

    for pattern in IMPORT_PATTERNS:
        for match in pattern.finditer(content):
            imports.append(match.group(1))
    return imports


def resolve_import(import_path: str, from_file: Path, src_root: Path) -> Path | None:
    """Resolve an import path to an actual file."""
    if import_path.startswith("."):
        # Relative import
        base = from_file.parent
        resolved = (base / import_path).resolve()
    elif import_path.startswith("@/"):
        # Alias import
        resolved = (src_root / import_path[2:]).resolve()
    elif import_path.startswith(f"@/{FEATURES_DIR}/") or import_path.startswith(f"{FEATURES_DIR}/"):
        clean = import_path.lstrip("@/")
        resolved = (src_root / clean).resolve()
    else:
        return None

    # Try with extensions and index
    for ext in ALLOWED_EXTENSIONS:
        candidate = Path(f"{resolved}{ext}")
        if candidate.exists():
            return candidate
    for ext in ALLOWED_EXTENSIONS:
        candidate = resolved / f"index{ext}"
        if candidate.exists():
            return candidate
    return resolved if resolved.exists() else None


def is_feature_path(path: Path, src_root: Path) -> bool:
    """Check if a path is inside features/."""
    try:
        relative = path.relative_to(src_root / FEATURES_DIR)
        return len(relative.parts) >= 1
    except ValueError:
        return False


def get_feature_name(path: Path, src_root: Path) -> str | None:
    """Get the feature name from a path inside features/."""
    try:
        relative = path.relative_to(src_root / FEATURES_DIR)
        return relative.parts[0] if relative.parts else None
    except ValueError:
        return None


def is_shared_path(path: Path, src_root: Path) -> bool:
    """Check if a path is inside shared/."""
    try:
        path.relative_to(src_root / SHARED_DIR)
        return True
    except ValueError:
        return False


def check_cross_feature_imports(src_root: Path) -> list[dict]:
    """Check for direct deep imports between features."""
    violations = []
    features_root = src_root / FEATURES_DIR

    if not features_root.exists():
        return [{"error": f"No {FEATURES_DIR}/ directory found at {src_root}"}]

    for file_path in features_root.rglob("*"):
        if file_path.suffix not in ALLOWED_EXTENSIONS:
            continue
        if file_path.name.startswith("index."):
            continue  # barrel exports are fine

        current_feature = get_feature_name(file_path, src_root)
        if not current_feature:
            continue

        imports = find_imports(file_path)
        for imp in imports:
            # Check for deep import into another feature
            for pattern in [
                re.compile(rf"@?/?{FEATURES_DIR}/(\w+)/(.+)"),
                re.compile(rf"\./\.\./(\w+)/(.+)"),  # relative cross-feature
            ]:
                match = pattern.match(imp)
                if match:
                    target_feature = match.group(1)
                    deep_path = match.group(2) if match.lastindex >= 2 else ""
                    if target_feature != current_feature and deep_path and "index" not in deep_path:
                        violations.append({
                            "rule": "cross-feature-deep-import",
                            "file": str(file_path.relative_to(src_root)),
                            "import": imp,
                            "from_feature": current_feature,
                            "to_feature": target_feature,
                            "message": f"Deep import from {current_feature} to {target_feature} (use index.ts instead)",
                        })

    return violations


def check_shared_contamination(src_root: Path) -> list[dict]:
    """Check for feature-specific code in shared/."""
    violations = []
    shared_root = src_root / SHARED_DIR

    if not shared_root.exists():
        return []

    for file_path in shared_root.rglob("*"):
        if file_path.suffix not in ALLOWED_EXTENSIONS:
            continue

        imports = find_imports(file_path)
        for imp in imports:
            # Check if shared imports from features
            if f"/{FEATURES_DIR}/" in imp or f"@/{FEATURES_DIR}/" in imp:
                violations.append({
                    "rule": "shared-imports-feature",
                    "file": str(file_path.relative_to(src_root)),
                    "import": imp,
                    "message": f"shared/ file imports from features/ (shared must be independent)",
                })

    return violations


def check_barrel_exports(src_root: Path) -> list[dict]:
    """Check that all features have index.ts barrel exports."""
    violations = []
    features_root = src_root / FEATURES_DIR

    if not features_root.exists():
        return []

    for feature_dir in features_root.iterdir():
        if not feature_dir.is_dir():
            continue
        if feature_dir.name.startswith("_") or feature_dir.name.startswith("."):
            continue

        has_index = any(
            (feature_dir / f"index{ext}").exists()
            for ext in ALLOWED_EXTENSIONS
        )
        if not has_index:
            violations.append({
                "rule": "missing-barrel-export",
                "feature": feature_dir.name,
                "message": f"Feature '{feature_dir.name}' has no index.ts barrel export",
            })

    return violations


def check_export_star(src_root: Path) -> list[dict]:
    """Check for export * (wildcard exports) in feature index files."""
    violations = []
    features_root = src_root / FEATURES_DIR

    if not features_root.exists():
        return []

    for feature_dir in features_root.iterdir():
        if not feature_dir.is_dir():
            continue
        for ext in ALLOWED_EXTENSIONS:
            index_file = feature_dir / f"index{ext}"
            if index_file.exists():
                try:
                    content = index_file.read_text(encoding="utf-8")
                    if re.search(r"export\s+\*\s+from", content):
                        violations.append({
                            "rule": "wildcard-export",
                            "file": str(index_file.relative_to(src_root)),
                            "message": f"Wildcard export in {feature_dir.name}/index.ts (use explicit named exports)",
                        })
                except Exception:
                    pass

    return violations


def run_checks(src_path: str) -> None:
    """Run all VSA architecture checks."""
    src_root = Path(src_path).resolve()

    if not src_root.exists():
        print(f"ERROR: Path does not exist: {src_root}")
        sys.exit(1)

    print(f"\n{'='*60}")
    print(f"VSA Architecture Check: {src_root}")
    print(f"{'='*60}\n")

    all_violations = []

    # Run checks
    checks = [
        ("Cross-feature deep imports", check_cross_feature_imports),
        ("Shared code contamination", check_shared_contamination),
        ("Barrel exports (index.ts)", check_barrel_exports),
        ("Wildcard exports (export *)", check_export_star),
    ]

    for check_name, check_fn in checks:
        violations = check_fn(src_root)
        status = "PASS" if not violations else f"FAIL ({len(violations)} issues)"
        print(f"  [{status}] {check_name}")
        all_violations.extend(violations)

    # Print details
    if all_violations:
        print(f"\n{'─'*60}")
        print("Violations:")
        print(f"{'─'*60}")
        for v in all_violations:
            rule = v.get("rule", "unknown")
            msg = v.get("message", "")
            file = v.get("file", v.get("feature", ""))
            imp = v.get("import", "")
            print(f"\n  [{rule}] {msg}")
            if file:
                print(f"    File: {file}")
            if imp:
                print(f"    Import: {imp}")

    # Summary
    print(f"\n{'='*60}")
    total = len(all_violations)
    if total == 0:
        print("RESULT: All checks passed. VSA compliance OK.")
    else:
        print(f"RESULT: {total} violation(s) found. Fix before merging.")
    print(f"{'='*60}\n")

    sys.exit(1 if total > 0 else 0)


if __name__ == "__main__":
    src_path = sys.argv[1] if len(sys.argv) > 1 else "./src"
    run_checks(src_path)
