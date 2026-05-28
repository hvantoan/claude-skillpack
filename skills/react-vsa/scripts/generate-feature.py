#!/usr/bin/env python3
"""Scaffold a new VSA feature slice for React/TypeScript projects.

Creates:
    features/{name}/
    ├── components/
    │   └── .gitkeep
    ├── hooks/
    │   └── .gitkeep
    ├── api/
    │   └── {name}-api.ts
    ├── types/
    │   └── {name}.types.ts
    ├── store/
    │   └── .gitkeep
    └── index.ts

Usage:
    python generate-feature.py <feature-name> [--path <src-dir>]

Examples:
    python generate-feature.py auth
    python generate-feature.py products --path ./src
    python generate-feature.py shopping-cart
"""

import argparse
import re
import sys
from pathlib import Path


def to_pascal_case(kebab: str) -> str:
    """Convert kebab-case to PascalCase."""
    return "".join(word.capitalize() for word in kebab.split("-"))


def to_camel_case(kebab: str) -> str:
    """Convert kebab-case to camelCase."""
    parts = kebab.split("-")
    return parts[0] + "".join(p.capitalize() for p in parts[1:])


def validate_name(name: str) -> bool:
    """Validate feature name is kebab-case."""
    return bool(re.match(r"^[a-z][a-z0-9]*(-[a-z0-9]+)*$", name))


def generate_api_file(name: str) -> str:
    """Generate API boilerplate."""
    camel = to_camel_case(name)
    pascal = to_pascal_case(name)
    return f"""import {{ apiClient }} from '@/shared/api/client';
import type {{ {pascal} }} from '../types/{name}.types';

export const {camel}Api = {{
  getAll: () => apiClient.get<{pascal}[]>('/{name}s'),
  getById: (id: string) => apiClient.get<{pascal}>(`/{name}s/${{id}}`),
  create: (data: Omit<{pascal}, 'id'>) => apiClient.post<{pascal}>(`/{name}s`, data),
  update: (id: string, data: Partial<{pascal}>) => apiClient.put<{pascal}>(`/{name}s/${{id}}`, data),
  delete: (id: string) => apiClient.delete(`/{name}s/${{id}}`),
}};
"""


def generate_types_file(name: str) -> str:
    """Generate types boilerplate."""
    pascal = to_pascal_case(name)
    return f"""export interface {pascal} {{
  id: string;
  name: string;
  createdAt: string;
  updatedAt: string;
}}
"""


def generate_index_file(name: str) -> str:
    """Generate barrel export file."""
    pascal = to_pascal_case(name)
    camel = to_camel_case(name)
    return f"""// {pascal} feature — public API
// Export only what other features need. No export *.

// Components — uncomment as you create them
// export {{ {pascal}Grid }} from './components/{name}-grid';

// Hooks — uncomment as you create them
// export {{ use{pascal} }} from './hooks/use-{name}';

// Types
export type {{ {pascal} }} from './types/{name}.types';
"""


def generate_store_file(name: str) -> str:
    """Generate Zustand store boilerplate."""
    pascal = to_pascal_case(name)
    camel = to_camel_case(name)
    return f"""import {{ create }} from 'zustand';
import type {{ {pascal} }} from '../types/{name}.types';

interface {pascal}State {{
  items: {pascal}[];
  selected: {pascal} | null;
  setItems: (items: {pascal}[]) => void;
  select: (item: {pascal} | null) => void;
}}

export const use{pascal}Store = create<{pascal}State>((set) => ({{
  items: [],
  selected: null,
  setItems: (items) => set({{ items }}),
  select: (selected) => set({{ selected }}),
}}));
"""


def create_feature(name: str, src_path: str) -> None:
    """Create the feature slice directory structure."""
    src_dir = Path(src_path).resolve()
    feature_dir = src_dir / "features" / name

    if feature_dir.exists():
        print(f"ERROR: Feature '{name}' already exists at {feature_dir}")
        sys.exit(1)

    # Create directories
    dirs = ["components", "hooks", "api", "types", "store"]
    for d in dirs:
        (feature_dir / d).mkdir(parents=True, exist_ok=True)

    # Create .gitkeep for empty dirs
    for d in ["components", "hooks", "store"]:
        (feature_dir / d / ".gitkeep").touch()

    # Generate files
    files = {
        f"api/{name}-api.ts": generate_api_file(name),
        f"types/{name}.types.ts": generate_types_file(name),
        f"store/{name}-store.ts": generate_store_file(name),
        "index.ts": generate_index_file(name),
    }

    for rel_path, content in files.items():
        file_path = feature_dir / rel_path
        file_path.write_text(content, encoding="utf-8")
        print(f"  Created: {file_path.relative_to(src_dir)}")

    # Summary
    print(f"\nFeature '{name}' created at: features/{name}/")
    print(f"\nNext steps:")
    print(f"  1. Create components in features/{name}/components/")
    print(f"  2. Create hooks in features/{name}/hooks/")
    print(f"  3. Update index.ts to export your components and hooks")
    print(f"  4. Import from '@/features/{name}' in other files")


def main() -> None:
    parser = argparse.ArgumentParser(description="Scaffold a new VSA feature slice")
    parser.add_argument("name", help="Feature name in kebab-case (e.g., 'auth', 'shopping-cart')")
    parser.add_argument("--path", default="./src", help="Path to src/ directory (default: ./src)")

    args = parser.parse_args()

    if not validate_name(args.name):
        print(f"ERROR: Feature name must be kebab-case (lowercase, hyphens). Got: '{args.name}'")
        print("Examples: auth, products, shopping-cart, user-profile")
        sys.exit(1)

    create_feature(args.name, args.path)


if __name__ == "__main__":
    main()
