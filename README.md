# claude-skillpack

[🇻🇳 Tiếng Việt](./README.vi.md) | 🇬🇧 English

Production-grade Claude Code skills for .NET, Go, React, TypeScript, PostgreSQL, and more. Install via `npx skills add`.

## Quick Start

### Install a single skill

```bash
npx skills add hvantoan/claude-skillpack@dotnet-vsa
```

### Install all skills from this repo

```bash
npx skills add hvantoan/claude-skillpack
```

### Install globally (available in all projects)

```bash
npx skills add hvantoan/claude-skillpack@golang-pro -g
```

## Skills

### .NET Development

| Skill | Description |
|-------|-------------|
| **[csharp-developer](./skills/csharp-developer/)** | C# / .NET 8+ / ASP.NET Core / Blazor / EF Core / MediatR |
| **[dotnet-core-expert](./skills/dotnet-core-expert/)** | .NET 8 minimal APIs / clean architecture / JWT / AOT |
| **[dotnet-vsa](./skills/dotnet-vsa/)** | Vertical Slice Architecture / FluentValidation / Refit+Polly / RabbitMQ / HMAC auth |

### Backend & Infrastructure

| Skill | Description |
|-------|-------------|
| **[golang-pro](./skills/golang-pro/)** | Go concurrency / gRPC / REST microservices / pprof / generics |
| **[microservices-architect](./skills/microservices-architect/)** | DDD / saga / event sourcing / CQRS / service mesh |
| **[postgres-pro](./skills/postgres-pro/)** | PostgreSQL query optimization / JSONB / replication / VACUUM |

### Frontend Development

| Skill | Description |
|-------|-------------|
| **[react-expert](./skills/react-expert/)** | React 18+ / Next.js App Router / Server Components / hooks |
| **[tanstack](./skills/tanstack/)** | TanStack Start / Form / AI streaming |
| **[tiptap](./skills/tiptap/)** | Tiptap rich text editor / React 19 / Tailwind v4 / shadcn |

### TypeScript & Code Quality

| Skill | Description |
|-------|-------------|
| **[typescript-pro](./skills/typescript-pro/)** | Advanced TypeScript / generics / tRPC / monorepo |
| **[typescript-react-reviewer](./skills/typescript-react-reviewer/)** | TypeScript + React 19 code review / anti-patterns |

## Architecture Verification (dotnet-vsa only)

The `dotnet-vsa` skill includes an architecture compliance checker:

```bash
./skills/dotnet-vsa/scripts/verify-architecture.sh [project-path]
```

Checks: project structure, IEndpoint convention, FluentValidation, HMAC security, resilience pipeline, RabbitMQ config, code style, testing, domain model quality, shared logic hygiene.

## Development

### Skill Structure

Each skill follows the [Claude Code skills format](https://docs.claude.com/en/docs/claude-code/skills):

```
skills/<skill-name>/
├── SKILL.md              # Main instructions (required, <300 lines)
├── references/           # Detailed docs loaded as-needed
├── scripts/              # Executable scripts
└── assets/               # Output resources
```

### Create a New Skill

Use [skill-creator](https://github.com/anthropics/skills) or create manually:

```bash
mkdir -p skills/my-skill
cat > skills/my-skill/SKILL.md << 'EOF'
---
name: my-skill
description: What this skill does and when to use it
---

# My Skill

Instructions that Claude follows when this skill is active.
EOF
```

### Run Install Scripts

Skills with Python/Node dependencies include install scripts:

```bash
cd skills
./install.sh        # Linux/macOS
./install.ps1       # Windows (PowerShell)
```

See [INSTALLATION.md](./skills/INSTALLATION.md) for details.

## License

MIT

---

Built with [Claude Code](https://claude.ai/code) • Skills powered by [npx skills](https://github.com/vercel-labs/skills)