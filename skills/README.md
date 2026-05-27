# Skills

[🇻🇳 Tiếng Việt](./README.vi.md) | 🇬🇧 English

Skills are folders of instructions, scripts, and resources that Claude loads dynamically to improve performance on specialized tasks. Skills teach Claude how to complete specific tasks in a repeatable way, whether that's creating documents with your company's brand guidelines, analyzing data using your organization's specific workflows, or automating personal tasks.

For more information, check out:
- [What are skills?](https://support.claude.com/en/articles/12512176-what-are-skills)
- [Using skills in Claude](https://support.claude.com/en/articles/12512180-using-skills-in-claude)
- [How to create custom skills](https://support.claude.com/en/articles/12512198-creating-custom-skills)
- [Equipping agents for the real world with Agent Skills](https://anthropic.com/engineering/equipping-agents-for-the-real-world-with-agent-skills)

# About This Repository

This repository contains example skills that demonstrate what's possible with Claude's skills system. These examples range from creative applications (art, music, design) to technical tasks (testing web apps, MCP server generation) to enterprise workflows (communications, branding, etc.).

Each skill is self-contained in its own directory with a `SKILL.md` file containing the instructions and metadata that Claude uses. Browse through these examples to get inspiration for your own skills or to understand different patterns and approaches.

The example skills in this repo are open source (Apache 2.0). We've also included the document creation & editing skills that power [Claude's document capabilities](https://www.anthropic.com/news/create-files) under the hood in the [`document-skills/`](./document-skills/) folder. These are source-available, not open source, but we wanted to share these with developers as a reference for more complex skills that are actively used in a production AI application.

**Note:** These are provided for demonstration and educational purposes only. While some of these capabilities may be available in Claude, the implementations and behaviors you receive from Claude may differ from what's shown in these examples. Always test skills thoroughly in your own environment before relying on them for critical tasks.

# Installation

Some skills require external dependencies (FFmpeg, ImageMagick, Node.js packages, Python packages). Use our automated installation scripts to set up all dependencies:

## Automated Installation (Recommended)

**Linux/macOS:**
```bash
cd $HOME/.claude/skills
./install.sh
```

**Windows (PowerShell as Administrator):**
```powershell
cd .claude\skills
.\install.ps1
```

The installation scripts will:
- Install system tools (FFmpeg, ImageMagick)
- Install Node.js packages (rmbg-cli, pnpm, wrangler, repomix)
- Create Python virtual environment
- Install Python packages (google-genai, pypdf, Pillow, etc.)
- Install test dependencies
- Verify all installations

## Manual Installation

For manual installation or troubleshooting, see [INSTALLATION.md](INSTALLATION.md) for detailed instructions.

## What Gets Installed

- **System Tools**: FFmpeg, ImageMagick
- **Node.js Packages**: rmbg-cli, pnpm, wrangler, repomix
- **Python Packages**: google-genai, pypdf, python-docx, Pillow, pytest

See [INSTALLATION.md](INSTALLATION.md) for complete dependency list and platform-specific instructions.

# Skill Catalog

## .NET Development

| Skill | Description | Triggers |
|-------|-------------|----------|
| **csharp-developer** | Build C# applications with .NET 8+, ASP.NET Core APIs, or Blazor web apps. REST APIs with minimal/controller routing, EF Core, CQRS via MediatR, Blazor components with state management. | C#, .NET, ASP.NET Core, Blazor, EF Core, Minimal API, MAUI, SignalR |
| **dotnet-core-expert** | Build .NET 8 applications with minimal APIs, clean architecture, or cloud-native microservices. JWT authentication, AOT compilation. | .NET 8, minimal API, clean architecture, EF Core, CQRS, MediatR |
| **dotnet-vsa** | Build .NET 8+ services with Vertical Slice Architecture, Minimal APIs, FluentValidation, Refit+Polly, and RabbitMQ. HMAC auth, resilience pipelines, architecture compliance verification. | dotnet, .NET, minimal API, vertical slice, FluentValidation, Refit, Polly, RabbitMQ, HMAC, endpoint, handler, validator |

## Backend & Infrastructure

| Skill | Description | Triggers |
|-------|-------------|----------|
| **golang-pro** | Concurrent Go patterns with goroutines/channels, microservices with gRPC/REST, performance optimization with pprof, idiomatic Go with generics and robust error handling. | goroutines, channels, Go generics, gRPC, CLI tools, benchmarks, table-driven testing |
| **microservices-architect** | Design distributed system architectures, decompose monoliths into bounded-context services, service boundaries, DDD, saga patterns, event sourcing, CQRS, service mesh, distributed tracing. | microservices, DDD, saga, event sourcing, CQRS, service mesh, distributed tracing |
| **postgres-pro** | Optimize PostgreSQL queries, configure replication, implement advanced features. EXPLAIN analysis, JSONB operations, extension usage, VACUUM tuning, performance monitoring. | PostgreSQL, EXPLAIN, JSONB, VACUUM, replication, query optimization |

## Frontend Development

| Skill | Description | Triggers |
|-------|-------------|----------|
| **react-expert** | Build React 18+ applications, Next.js App Router projects, or create-react-app setups. Server Components, Suspense, useActionState, performance optimization, React 19 features. | React, Next.js, Server Components, Suspense, hooks, state management |
| **tanstack** | Build with TanStack Start (full-stack React), TanStack Form (headless form management), and TanStack AI (AI streaming/chat). Routes, server functions, forms, validation. | TanStack Start, Form, Router, AI features |
| **tiptap** | Build rich text editors with Tiptap (open-source, free tier). React 19, Tailwind v4, shadcn/ui. Editor setup, SSR config, image uploads, free extensions, markdown, prose styling. | Tiptap, rich text editor, WYSIWYG, prose styling |

## TypeScript & Code Quality

| Skill | Description | Triggers |
|-------|-------------|----------|
| **typescript-pro** | Advanced TypeScript type systems, custom type guards, utility types, branded types, tRPC for end-to-end type safety. Monorepo setup, conditional/mapped types, discriminated unions. | TypeScript generics, conditional types, mapped types, tRPC, monorepo |
| **typescript-react-reviewer** | Expert code reviewer for TypeScript + React 19. Anti-pattern detection, state management evaluation, code smell identification, TypeScript type safety checks. | code review, PR review, React architecture, useEffect abuse, type safety |

# Document Skills

The `document-skills/` subdirectory contains skills that Anthropic developed to help Claude create various document file formats:

- **docx** - Create, edit, and analyze Word documents with tracked changes, comments, formatting preservation, and text extraction
- **pdf** - Comprehensive PDF manipulation: text/table extraction, creation, merging/splitting, form handling
- **pptx** - Create, edit, and analyze PowerPoint presentations with layouts, templates, charts, and automated slide generation
- **xlsx** - Create, edit, and analyze Excel spreadsheets with formulas, formatting, data analysis, and visualization

**Important Disclaimer:** These document skills are point-in-time snapshots and are not actively maintained or updated. They are primarily intended as reference examples.

# Try in Claude Code, Claude.ai, and the API

## Claude Code
Register this repository as a Claude Code Plugin marketplace:
```
/plugin marketplace add anthropics/skills
```

## Claude.ai
These example skills are available to paid plans in Claude.ai. See [Using skills in Claude](https://support.claude.com/en/articles/12512180-using-skills-in-claude#h_a4222fa77b).

## Claude API
Use Anthropic's pre-built skills and upload custom skills via the [Skills API Quickstart](https://docs.claude.com/en/api/skills-guide#creating-a-skill).

# Creating a Basic Skill

Skills are simple to create — just a folder with a `SKILL.md` file:

```markdown
---
name: my-skill-name
description: A clear description of what this skill does and when to use it
---

# My Skill Name

[Instructions that Claude will follow when this skill is active]

## Examples
- Example usage 1
- Example usage 2

## Guidelines
- Guideline 1
- Guideline 2
```

Required frontmatter fields:
- `name` - Unique identifier (lowercase, hyphens for spaces)
- `description` - What the skill does and when to use it

For more details, see [How to create custom skills](https://support.claude.com/en/articles/12512198-creating-custom-skills).

# Partner Skills

Skills are a great way to teach Claude how to get better at using specific pieces of software. As we see awesome example skills from partners, we may highlight some of them here:

- **Notion** - [Notion Skills for Claude](https://www.notion.so/notiondevs/Notion-Skills-for-Claude-28da4445d27180c7af1df7d8615723d0)