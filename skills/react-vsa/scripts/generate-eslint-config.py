#!/usr/bin/env python3
"""Generate ESLint + Prettier + .editorconfig for VSA/FSD React projects.

Reads template assets from assets/eslint/ and composes a config based on
architecture type, enforcement mode, and project structure.

Usage:
    python generate-eslint-config.py [options]
    python generate-eslint-config.py  # interactive mode

Examples:
    python generate-eslint-config.py --arch=vsa --enforcement=boundaries
    python generate-eslint-config.py --arch=fsd --enforcement=boundaries --formatting
    python generate-eslint-config.py --arch=vsa --enforcement=minimal --features=auth,products,cart
    python generate-eslint-config.py --dry-run --framework=nextjs
"""

import argparse
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_DIR = SCRIPT_DIR.parent
ASSETS_DIR = SKILL_DIR / "assets" / "eslint"


# ---------------------------------------------------------------------------
# Project detection
# ---------------------------------------------------------------------------

def find_git_root(start: Path) -> Path | None:
    """Walk up from start to find .git directory."""
    current = start.resolve()
    for _ in range(20):
        if (current / ".git").exists():
            return current
        parent = current.parent
        if parent == current:
            break
        current = parent
    return None


def detect_project_structure(output_path: str) -> dict:
    """Detect monorepo, existing configs, and project type."""
    target = Path(output_path).resolve()
    git_root = find_git_root(target)

    has_packages = git_root and (git_root / "packages").exists() and bool(list((git_root / "packages").iterdir()))
    has_apps = git_root and (git_root / "apps").exists() and bool(list((git_root / "apps").iterdir()))
    is_monorepo = has_packages or has_apps

    existing = {}
    for name in [".editorconfig", ".prettierrc", ".prettierrc.json", "eslint.config.mjs", "eslint.config.js"]:
        paths_to_check = [target / name]
        if git_root and git_root != target:
            paths_to_check.append(git_root / name)
        for p in paths_to_check:
            if p.exists():
                existing[name] = p

    has_dotnet = False
    if git_root:
        has_dotnet = bool(list(git_root.glob("**/*.csproj"))[:5])

    return {
        "target": target,
        "git_root": git_root,
        "is_monorepo": is_monorepo,
        "existing_configs": existing,
        "has_dotnet": has_dotnet,
    }


# ---------------------------------------------------------------------------
# Interactive prompts
# ---------------------------------------------------------------------------

def ask_choice(prompt: str, options: list[str], default: str | None = None) -> str:
    """Ask user to pick from options."""
    opts = "/".join(f"[{o[0]}]{o[1:]}" if o == default else o for o in options)
    while True:
        answer = input(f"{prompt} ({opts}): ").strip().lower()
        if not answer and default:
            return default
        for o in options:
            if o.startswith(answer) or o == answer:
                return o
        print(f"  Invalid choice. Pick from: {', '.join(options)}")


def ask_yes_no(prompt: str, default: bool = False) -> bool:
    """Ask yes/no question."""
    suffix = " [Y/n]" if default else " [y/N]"
    while True:
        answer = input(f"{prompt}{suffix}: ").strip().lower()
        if not answer:
            return default
        if answer in ("y", "yes"):
            return True
        if answer in ("n", "no"):
            return False


def interactive_prompts(structure: dict, args: argparse.Namespace) -> dict:
    """Fill in missing args via interactive prompts."""
    config = {
        "arch": args.arch,
        "enforcement": args.enforcement,
        "features": args.features,
        "framework": args.framework,
        "formatting": args.formatting,
        "existing_config": args.existing_config,
    }

    if not config["arch"]:
        config["arch"] = ask_choice("Architecture?", ["vsa", "fsd", "custom"], "vsa")

    if not config["enforcement"]:
        config["enforcement"] = ask_choice("Enforcement?", ["boundaries", "minimal", "none"], "boundaries")

    if config["enforcement"] == "minimal" and not config["features"]:
        features_input = input("Feature names (comma-separated): ").strip()
        config["features"] = [f.strip() for f in features_input.split(",") if f.strip()] if features_input else []

    if not config["framework"]:
        config["framework"] = ask_choice("Framework?", ["nextjs", "vite", "other"], "vite")

    if config["formatting"] is None:
        config["formatting"] = ask_yes_no("Include Prettier + .editorconfig?", False)

    if structure["existing_configs"] and not config["existing_config"]:
        print(f"\n  Found existing configs: {', '.join(structure['existing_configs'].keys())}")
        config["existing_config"] = ask_choice("How to handle?", ["skip", "append", "overwrite"], "skip")

    return config


# ---------------------------------------------------------------------------
# Template composition
# ---------------------------------------------------------------------------

def load_template(name: str) -> str:
    """Load a template file from assets/eslint/."""
    path = ASSETS_DIR / name
    if not path.exists():
        print(f"ERROR: Template not found: {path}")
        sys.exit(1)
    return path.read_text(encoding="utf-8")


def compose_eslint_config(config: dict) -> str:
    """Compose the final eslint.config.mjs from templates."""
    base = load_template("base.config.mjs")
    arch = config["arch"]
    enforcement = config["enforcement"]

    if enforcement == "none":
        # Just base config, no boundary rules
        return base.replace(
            "  // BOUNDARY_CONFIG_INSERTION_POINT — harness injects boundary rules here\n",
            ""
        )

    # Determine which boundary template to use
    if arch == "fsd" and enforcement == "boundaries":
        boundary_template = load_template("fsd-boundaries.config.mjs")
    elif arch in ("vsa", "custom") and enforcement == "boundaries":
        boundary_template = load_template("vsa-boundaries.config.mjs")
    elif enforcement == "minimal":
        boundary_template = load_template("vsa-minimal.config.mjs")
    else:
        return base

    # Handle FEATURE_NAMES replacement for minimal mode
    if enforcement == "minimal" and config.get("features"):
        features = config["features"]
        feature_patterns = []
        for f in features:
            feature_patterns.append(
                f'          {{ group: ["@/features/{f}/**"], '
                f'message: "VSA: Use \'@/features/{f}\' (public API only)." }},'
            )
        feature_block = "\n".join(feature_patterns) + "\n"
        boundary_template = boundary_template.replace(
            "          // FEATURE_NAMES_START — harness replaces this block\n"
            "          // Example generated pattern:\n"
            "          // { group: [\"@/features/auth/**\"], message: \"VSA: Use '@/features/auth' (public API only).\" },\n"
            "          // FEATURE_NAMES_END",
            feature_block.rstrip(","),
        )

    # Extract imports from boundary template
    boundary_imports = []
    for line in boundary_template.split("\n"):
        stripped = line.strip()
        if stripped.startswith("import ") and stripped.endswith(";"):
            boundary_imports.append(stripped)

    # Extract the config object from boundary template (skip import + export lines)
    boundary_body_lines = []
    in_export = False
    brace_depth = 0
    for line in boundary_template.split("\n"):
        stripped = line.strip()
        if stripped.startswith("import "):
            continue
        if stripped.startswith("export const "):
            # Skip the export declaration line, capture the object
            in_export = True
            brace_depth += stripped.count("{") - stripped.count("}")
            # Add the object content after the first {
            after_eq = stripped.split("=", 1)[1].strip()
            if after_eq.startswith("{"):
                boundary_body_lines.append("  " + after_eq)
            continue
        if in_export:
            boundary_depth_delta = line.count("{") - line.count("}")
            brace_depth += boundary_depth_delta
            boundary_body_lines.append(line)
            if brace_depth <= 0:
                in_export = False

    # Strip trailing export closing brace — the base template already has );
    if boundary_body_lines and boundary_body_lines[-1].strip().rstrip(",") in ("};", "},"):
        boundary_body_lines[-1] = boundary_body_lines[-1].replace("};", "}").replace("},", "},")
        # Ensure consistent 2-space indent for the spliced block
        boundary_body_lines = [
            ("  " + line) if line.strip() and not line.startswith("  ") else line
            for line in boundary_body_lines
        ]

    # Compose: add imports + spread boundary config at insertion point
    # Add boundary imports to top of file
    base_lines = base.split("\n")
    new_lines = []
    existing_imports = set()
    added_boundary_imports = False

    for line in base_lines:
        stripped = line.strip()
        if stripped.startswith("import "):
            existing_imports.add(stripped)

        # Insert boundary imports before first import if not already added
        if not added_boundary_imports and stripped.startswith("import "):
            if not new_lines:
                new_lines.append(line)
            else:
                new_lines.append(line)
        elif not added_boundary_imports and stripped.startswith("//") and not any(l.startswith("import ") for l in new_lines):
            new_lines.append(line)
        else:
            new_lines.append(line)

        if not added_boundary_imports and stripped.startswith("import "):
            added_boundary_imports = True
            # Add any new imports from boundary template
            for bi in boundary_imports:
                if bi not in existing_imports:
                    new_lines.append(bi)

    result = "\n".join(new_lines)

    # Replace insertion point with boundary config
    insertion_marker = "  // BOUNDARY_CONFIG_INSERTION_POINT — harness injects boundary rules here"
    if insertion_marker in result:
        # Build the config block
        config_block = "\n".join(boundary_body_lines)
        result = result.replace(
            insertion_marker,
            config_block.rstrip(),
        )

    return result


def compose_prettierrc() -> str:
    """Load and return prettier config."""
    return load_template("prettierrc.template.json")


def compose_editorconfig(mode: str, existing_content: str | None = None) -> str:
    """Compose .editorconfig content."""
    if mode == "full" or not existing_content:
        return load_template("editorconfig-full.ini")
    elif mode == "append" and existing_content:
        append_sections = load_template("editorconfig-append.ini")
        return existing_content.rstrip("\n") + "\n\n" + append_sections
    return existing_content or ""


# ---------------------------------------------------------------------------
# File writing
# ---------------------------------------------------------------------------

def write_file(path: Path, content: str, dry_run: bool, action: str = "Created") -> None:
    """Write file or print if dry-run."""
    if dry_run:
        print(f"  [DRY-RUN] Would write: {path}")
        print(f"    ({len(content)} bytes)")
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    print(f"  {action}: {path}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def build_install_command(config: dict) -> str:
    """Build npm install command for required deps."""
    deps = ["eslint", "typescript-eslint", "eslint-plugin-react-hooks",
            "eslint-plugin-react-refresh", "eslint-plugin-import",
            "eslint-import-resolver-typescript"]
    if config["enforcement"] == "boundaries":
        deps.append("eslint-plugin-boundaries")
    return "npm i -D " + " \\\n    ".join(deps)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate ESLint + Prettier + .editorconfig for VSA/FSD React projects",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Examples:
  python generate-eslint-config.py --arch=vsa --enforcement=boundaries
  python generate-eslint-config.py --arch=fsd --enforcement=boundaries --formatting
  python generate-eslint-config.py --arch=vsa --enforcement=minimal --features=auth,products,cart
  python generate-eslint-config.py --dry-run --framework=nextjs""",
    )
    parser.add_argument("--output", default=".", help="Target directory (default: .)")
    parser.add_argument("--arch", choices=["vsa", "fsd", "custom"], help="Project architecture")
    parser.add_argument("--enforcement", choices=["boundaries", "minimal", "none"], help="Boundary enforcement mode")
    parser.add_argument("--features", help="Comma-separated feature names (for minimal mode)")
    parser.add_argument("--framework", choices=["nextjs", "vite", "other"], help="Framework extras")
    parser.add_argument("--formatting", action="store_true", default=None, help="Include Prettier + .editorconfig")
    parser.add_argument("--no-formatting", dest="formatting", action="store_false", help="Skip formatting configs")
    parser.add_argument("--existing-config", choices=["skip", "append", "overwrite"], help="How to handle existing configs")
    parser.add_argument("--dry-run", action="store_true", help="Preview without writing files")

    args = parser.parse_args()

    # Detect project structure
    structure = detect_project_structure(args.output)

    # Determine if interactive mode needed
    needs_interactive = not args.arch or not args.enforcement
    if needs_interactive:
        config = interactive_prompts(structure, args)
    else:
        config = {
            "arch": args.arch,
            "enforcement": args.enforcement,
            "features": [f.strip() for f in args.features.split(",")] if args.features else [],
            "framework": args.framework or "vite",
            "formatting": args.formatting if args.formatting is not None else False,
            "existing_config": args.existing_config or "skip",
        }

    target = structure["target"]
    dry_run = args.dry_run

    print(f"\nGenerating ESLint config for: {config['arch']} + {config['enforcement']}")
    print(f"Target: {target}\n")

    # 1. Generate eslint.config.mjs
    existing_eslint = structure["existing_configs"].get("eslint.config.mjs")
    existing_prettierrc = structure["existing_configs"].get(".prettierrc") or structure["existing_configs"].get(".prettierrc.json")
    existing_editorconfig = structure["existing_configs"].get(".editorconfig")

    should_write_eslint = True
    if existing_eslint:
        action = config["existing_config"]
        if action == "skip":
            print(f"  Skipping eslint.config.mjs (already exists: {existing_eslint})")
            should_write_eslint = False
        elif action == "overwrite":
            should_write_eslint = True
        else:
            should_write_eslint = True

    if should_write_eslint:
        eslint_content = compose_eslint_config(config)

        # Framework-specific adjustments
        if config["framework"] == "nextjs":
            if "**/.next/**" not in eslint_content:
                eslint_content = eslint_content.replace(
                    '      "**/dist/**"',
                    '      "**/dist/**",\n      "**/.next/**"',
                )

        write_file(target / "eslint.config.mjs", eslint_content, dry_run)

    # 2. Generate .prettierrc.json
    if config["formatting"]:
        if existing_prettierrc and config["existing_config"] == "skip":
            print(f"  Skipping .prettierrc.json (already exists: {existing_prettierrc})")
        else:
            prettier_content = compose_prettierrc()
            write_file(target / ".prettierrc.json", prettier_content, dry_run)

    # 3. Generate .editorconfig
    if config["formatting"]:
        if existing_editorconfig and config["existing_config"] == "skip":
            print(f"  Skipping .editorconfig (already exists: {existing_editorconfig})")
        elif existing_editorconfig and config["existing_config"] == "append":
            existing_content = existing_editorconfig.read_text(encoding="utf-8")
            ec_content = compose_editorconfig("append", existing_content)
            write_file(existing_editorconfig, ec_content, dry_run, action="Appended to")
        else:
            ec_content = compose_editorconfig("full")
            write_file(target / ".editorconfig", ec_content, dry_run)

    # Summary
    print(f"\n{'[DRY-RUN] ' if dry_run else ''}Generation complete.")
    print(f"\nInstall dependencies:\n  {build_install_command(config)}")
    print("\nAdd to package.json scripts:")
    print('  "lint": "eslint src/"')
    print('  "lint:fix": "eslint src/ --fix"')


if __name__ == "__main__":
    main()
