#!/usr/bin/env python3
"""Generate .editorconfig for .NET VSA projects.

Usage:
    python3 generate-editorconfig.py [output-path]

Default output: .editorconfig in current directory.
"""

import os
import sys

EDITORCONFIG = """# .editorconfig — .NET VSA Project Style
# https://editorconfig.org

root = true

[*]
charset = utf-8
end_of_line = lf
insert_final_newline = true
trim_trailing_whitespace = true
indent_style = space
indent_size = 4

[*.cs]
# --- Naming ---
# Private fields: _camelCase
dotnet_naming_rule.private_fields_should_be_camel_case_with_underscore.severity = warning
dotnet_naming_rule.private_fields_should_be_camel_case_with_underscore.symbols = private_fields
dotnet_naming_rule.private_fields_should_be_camel_case_with_underscore.style = underscore_camel_case

dotnet_naming_symbols.private_fields.applicable_kinds = field
dotnet_naming_symbols.private_fields.applicable_accessibilities = private, protected, protected_internal, private_protected
dotnet_naming_symbols.private_fields.required_modifiers =

dotnet_naming_style.underscore_camel_case.capitalization = camel_case
dotnet_naming_style.underscore_camel_case.required_prefix = _

# Constants: PascalCase
dotnet_naming_rule.constants_should_be_pascal_case.severity = warning
dotnet_naming_rule.constants_should_be_pascal_case.symbols = constants
dotnet_naming_rule.constants_should_be_pascal_case.style = pascal_case

dotnet_naming_symbols.constants.applicable_kinds = field, local
dotnet_naming_symbols.constants.required_modifiers = const
dotnet_naming_symbols.constants.applicable_accessibilities = *

dotnet_naming_style.pascal_case.capitalization = pascal_case

# Interfaces: IPascalCase
dotnet_naming_rule.interfaces_should_begin_with_i.severity = warning
dotnet_naming_rule.interfaces_should_begin_with_i.symbols = interfaces
dotnet_naming_rule.interfaces_should_begin_with_i.style = begins_with_i

dotnet_naming_symbols.interfaces.applicable_kinds = interface
dotnet_naming_symbols.interfaces.applicable_accessibilities = *

dotnet_naming_style.begins_with_i.capitalization = pascal_case
dotnet_naming_style.begins_with_i.required_prefix = I

# Public members: PascalCase
dotnet_naming_rule.public_members_should_be_pascal_case.severity = warning
dotnet_naming_rule.public_members_should_be_pascal_case.symbols = public_symbols
dotnet_naming_rule.public_members_should_be_pascal_case.style = pascal_case

dotnet_naming_symbols.public_symbols.applicable_kinds = property, method, event, delegate
dotnet_naming_symbols.public_symbols.applicable_accessibilities = public

# --- Code Style ---
# var for obvious types, explicit for ambiguous
csharp_style_var_for_built_in_types = false:suggestion
csharp_style_var_when_type_is_apparent = true:suggestion
csharp_style_var_elsewhere = true:suggestion

# Expression-bodied members
csharp_style_expression_bodied_methods = when_on_single_line:suggestion
csharp_style_expression_bodied_properties = true:suggestion
csharp_style_expression_bodied_accessors = true:suggestion

# Pattern matching
csharp_style_pattern_matching_over_is_with_cast_check = true:suggestion
csharp_style_pattern_matching_over_as_with_null_check = true:suggestion

# Switch expressions
csharp_style_prefer_switch_expression = true:suggestion

# Using directives
csharp_using_directive_placement = outside_namespace:warning
dotnet_sort_system_directives_first = true

# Namespace style (file-scoped)
csharp_style_namespace_declarations = file_scoped:warning

# Brace style (Egyptian / K&R)
csharp_prefer_braces = true:suggestion
csharp_prefer_simple_using_statement = true:suggestion

# Null checking
csharp_style_throw_expression = true:suggestion
csharp_style_conditional_delegate_call = true:suggestion
dotnet_style_coalesce_expression = true:suggestion
dotnet_style_null_propagation = true:suggestion

# New line preferences
csharp_new_line_before_open_brace = all
csharp_new_line_before_else = true
csharp_new_line_before_catch = true
csharp_new_line_before_finally = true
csharp_new_line_before_members_in_object_initializers = true
csharp_new_line_before_members_in_anonymous_types = true

# Indentation
csharp_indent_case_contents = true
csharp_indent_switch_labels = true
csharp_indent_block_contents = true
csharp_indent_braces = false

# Spacing
csharp_space_after_cast = false
csharp_space_after_keywords_in_control_flow_statements = true
csharp_space_between_parentheses = false
csharp_space_before_colon_in_inheritance_clause = true
csharp_space_after_colon_in_inheritance_clause = true

# Wrapping
csharp_preserve_single_line_statements = true
csharp_preserve_single_line_blocks = true

# Analyzers
dotnet_diagnostic.IDE0003.severity = suggestion    # this qualification
dotnet_diagnostic.IDE0009.severity = suggestion    # remove unnecessary this
dotnet_diagnostic.IDE0058.severity = suggestion    # expression value is never used
dotnet_diagnostic.CS1591.severity = none            # missing XML doc comment

[*.csproj]
indent_size = 2

[*.{json,yaml,yml}]
indent_size = 2

[*.md]
indent_size = 2
trim_trailing_whitespace = false

[*.{sh,bash}]
indent_size = 2

[Dockerfile]
indent_size = 2

[*.dockerfile]
indent_size = 2

[*.sql]
indent_size = 2
"""

def main():
    output = sys.argv[1] if len(sys.argv) > 1 else ".editorconfig"

    if os.path.exists(output):
        print(f"⚠  {output} already exists. Backing up to {output}.bak")
        os.rename(output, f"{output}.bak")

    with open(output, "w", encoding="utf-8") as f:
        f.write(EDITORCONFIG.strip() + "\n")

    print(f"✓  Generated {output}")
    print(f"   Includes: C# naming, formatting, namespace, brace style, and more")

if __name__ == "__main__":
    main()