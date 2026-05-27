# claude-skillpack

[🇻🇳 Tiếng Việt](./README.vi.md) | 🇬🇧 [English](./README.md)

Các skill Claude Code chất lượng sản xuất cho .NET, Go, React, TypeScript, PostgreSQL và hơn nữa. Cài đặt qua `npx skills add`.

## Cài đặt nhanh

### Cài một skill

```bash
npx skills add hvantoan/claude-skillpack@dotnet-vsa
```

### Cài tất cả skills từ repo

```bash
npx skills add hvantoan/claude-skillpack
```

### Cài toàn cục (dùng được ở mọi project)

```bash
npx skills add hvantoan/claude-skillpack@golang-pro -g
```

## Skills

### Phát triển .NET

| Skill | Mô tả |
|-------|-------|
| **[csharp-developer](./skills/csharp-developer/)** | C# / .NET 8+ / ASP.NET Core / Blazor / EF Core / MediatR |
| **[dotnet-core-expert](./skills/dotnet-core-expert/)** | .NET 8 minimal APIs / clean architecture / JWT / AOT |
| **[dotnet-vsa](./skills/dotnet-vsa/)** | Vertical Slice Architecture / FluentValidation / Refit+Polly / RabbitMQ / HMAC auth |

### Backend & Hạ tầng

| Skill | Mô tả |
|-------|-------|
| **[golang-pro](./skills/golang-pro/)** | Go concurrency / gRPC / REST microservices / pprof / generics |
| **[microservices-architect](./skills/microservices-architect/)** | DDD / saga / event sourcing / CQRS / service mesh |
| **[postgres-pro](./skills/postgres-pro/)** | Tối ưu PostgreSQL / JSONB / replication / VACUUM |

### Phát triển Frontend

| Skill | Mô tả |
|-------|-------|
| **[react-expert](./skills/react-expert/)** | React 18+ / Next.js App Router / Server Components / hooks |
| **[tanstack](./skills/tanstack/)** | TanStack Start / Form / AI streaming |
| **[tiptap](./skills/tiptap/)** | Tiptap rich text editor / React 19 / Tailwind v4 / shadcn |

### TypeScript & Chất lượng Code

| Skill | Mô tả |
|-------|-------|
| **[typescript-pro](./skills/typescript-pro/)** | TypeScript nâng cao / generics / tRPC / monorepo |
| **[typescript-react-reviewer](./skills/typescript-react-reviewer/)** | Review code TypeScript + React 19 / anti-patterns |

## Kiểm tra kiến trúc (dotnet-vsa)

Skill `dotnet-vsa` có script kiểm tra tuân thủ kiến trúc:

```bash
./skills/dotnet-vsa/scripts/verify-architecture.sh [project-path]
```

Kiểm tra: cấu trúc project, IEndpoint convention, FluentValidation, HMAC security, resilience pipeline, RabbitMQ config, code style, testing, domain model, shared logic hygiene.

## Phát triển

### Cấu trúc Skill

Mỗi skill tuân theo [định dạng Claude Code skills](https://docs.claude.com/en/docs/claude-code/skills):

```
skills/<tên-skill>/
├── SKILL.md              # Hướng dẫn chính (bắt buộc, <300 dòng)
├── references/           # Tài liệu chi tiết (tải khi cần)
├── scripts/              # Script thực thi
└── assets/               # Tài nguyên đầu ra
```

### Tạo Skill mới

Dùng [skill-creator](https://github.com/anthropics/skills) hoặc tạo thủ công:

```bash
mkdir -p skills/my-skill
cat > skills/my-skill/SKILL.md << 'EOF'
---
name: my-skill
description: Mô tả skill và khi nào sử dụng
---

# My Skill

Hướng dẫn mà Claude sẽ theo khi skill này được kích hoạt.
EOF
```

### Chạy Install Scripts

Skills có phụ thuộc Python/Node bao gồm install scripts:

```bash
cd skills
./install.sh        # Linux/macOS
./install.ps1       # Windows (PowerShell)
```

Xem [INSTALLATION.md](./skills/INSTALLATION.md) để biết chi tiết.

## Giấy phép

MIT

---

Xây dựng với [Claude Code](https://claude.ai/code) • Skills phân phối bởi [npx skills](https://github.com/vercel-labs/skills)