# Skills (Tiếng Việt)

Skills là các thư mục chứa hướng dẫn, script, và tài nguyên mà Claude tải động để cải thiện hiệu suất trên các tác vụ chuyên biệt. Skills dạy Claude cách hoàn thành các tác vụ cụ thể một cách có thể lặp lại, cho dù đó là tạo tài liệu theo hướng dẫn thương hiệu, phân tích dữ liệu theo quy trình của tổ chức, hay tự động hóa các công việc cá nhân.

Thêm thông tin:
- [Skills là gì?](https://support.claude.com/en/articles/12512176-what-are-skills)
- [Sử dụng Skills trong Claude](https://support.claude.com/en/articles/12512180-using-skills-in-claude)
- [Cách tạo skill tùy chỉnh](https://support.claude.com/en/articles/12512198-creating-custom-skills)
- [Trang bị agent cho thế giới thực với Agent Skills](https://anthropic.com/engineering/equipping-agents-for-the-real-world-with-agent-skills)

# Giới thiệu Repository

Repository này chứa các skill mẫu minh họa những gì có thể làm với hệ thống skills của Claude. Các mẫu trải dài từ ứng dụng sáng tạo (nghệ thuật, âm nhạc, thiết kế) đến tác vụ kỹ thuật (kiểm thử web app, tạo MCP server) đến quy trình doanh nghiệp (truyền thông, thương hiệu, v.v.).

Mỗi skill nằm trong thư mục riêng với file `SKILL.md` chứa hướng dẫn và metadata mà Claude sử dụng. Duyệt qua các mẫu này để lấy cảm hứng hoặc hiểu các pattern và cách tiếp cận khác nhau.

Các skill mẫu trong repo này là mã nguồn mở (Apache 2.0). Chúng tôi cũng bao gồm các skill tạo & chỉnh sửa tài liệu hỗ trợ [khả năng tài liệu của Claude](https://www.anthropic.com/news/create-files) trong thư mục [`document-skills/`](./document-skills/).

**Lưu ý:** Các skill này chỉ dùng cho mục đích minh họa và giáo dục. Các triển khai thực tế có thể khác với những gì hiển thị trong mẫu. Luôn kiểm tra kỹ trong môi trường của bạn trước khi sử dụng cho tác vụ quan trọng.

# Cài đặt

Một số skill yêu cầu phụ thuộc bên ngoài (FFmpeg, ImageMagick, gói Node.js, gói Python). Sử dụng script cài đặt tự động:

## Cài đặt tự động (Khuyến nghị)

**Linux/macOS:**
```bash
cd $HOME/.claude/skills
./install.sh
```

**Windows (PowerShell với quyền Administrator):**
```powershell
cd .claude\skills
.\install.ps1
```

Script cài đặt sẽ:
- Cài đặt công cụ hệ thống (FFmpeg, ImageMagick)
- Cài đặt gói Node.js (rmbg-cli, pnpm, wrangler, repomix)
- Tạo môi trường ảo Python
- Cài đặt gói Python (google-genai, pypdf, Pillow, v.v.)
- Cài đặt phụ thuộc kiểm thử
- Xác minh tất cả đã cài đặt

## Cài đặt thủ công

Xem [INSTALLATION.md](INSTALLATION.md) để biết hướng dẫn chi tiết theo nền tảng.

## Những gì được cài đặt

- **Công cụ hệ thống**: FFmpeg, ImageMagick
- **Gói Node.js**: rmbg-cli, pnpm, wrangler, repomix
- **Gói Python**: google-genai, pypdf, python-docx, Pillow, pytest

# Danh mục Skills

## Phát triển .NET

| Skill | Mô tả | Kích hoạt khi |
|-------|-------|---------------|
| **csharp-developer** | Xây dựng ứng dụng C# với .NET 8+, ASP.NET Core API, hoặc Blazor. REST API với minimal/controller routing, EF Core, CQRS qua MediatR, Blazor components với state management. | C#, .NET, ASP.NET Core, Blazor, EF Core, Minimal API, MAUI, SignalR |
| **dotnet-core-expert** | Xây dựng ứng dụng .NET 8 với minimal API, clean architecture, hoặc cloud-native microservices. JWT authentication, AOT compilation. | .NET 8, minimal API, clean architecture, EF Core, CQRS, MediatR |
| **dotnet-vsa** | Xây dựng dịch vụ .NET 8+ với Vertical Slice Architecture, Minimal APIs, FluentValidation, Refit+Polly, và RabbitMQ. Xác thực HMAC, resilience pipelines, kiểm tra tuân thủ kiến trúc. | dotnet, .NET, minimal API, vertical slice, FluentValidation, Refit, Polly, RabbitMQ, HMAC, endpoint, handler, validator |

## Backend & Hạ tầng

| Skill | Mô tả | Kích hoạt khi |
|-------|-------|---------------|
| **golang-pro** | Concurrent Go patterns với goroutines/channels, microservices với gRPC/REST, tối ưu hiệu suất với pprof, Go idiomatic với generics và error handling vững chắc. | goroutines, channels, Go generics, gRPC, CLI tools, benchmarks, table-driven testing |
| **microservices-architect** | Thiết kế kiến trúc hệ thống phân tán, phân rã monolith thành bounded-context services, service boundaries, DDD, saga patterns, event sourcing, CQRS, service mesh, distributed tracing. | microservices, DDD, saga, event sourcing, CQRS, service mesh, distributed tracing |
| **postgres-pro** | Tối ưu truy vấn PostgreSQL, cấu hình replication, triển khai tính năng nâng cao. Phân tích EXPLAIN, JSONB operations, extension usage, VACUUM tuning, giám sát hiệu suất. | PostgreSQL, EXPLAIN, JSONB, VACUUM, replication, tối ưu truy vấn |

## Phát triển Frontend

| Skill | Mô tả | Kích hoạt khi |
|-------|-------|---------------|
| **react-expert** | Xây dựng ứng dụng React 18+, dự án Next.js App Router, hoặc create-react-app. Server Components, Suspense, useActionState, tối ưu hiệu suất, React 19. | React, Next.js, Server Components, Suspense, hooks, state management |
| **tanstack** | Xây dựng với TanStack Start (React full-stack), TanStack Form (form management headless), và TanStack AI (AI streaming/chat). Routes, server functions, forms, validation. | TanStack Start, Form, Router, AI features |
| **tiptap** | Xây dựng rich text editor với Tiptap (open-source, miễn phí). React 19, Tailwind v4, shadcn/ui. Cài đặt editor, SSR config, image uploads, extensions miễn phí, markdown, prose styling. | Tiptap, rich text editor, WYSIWYG, prose styling |

## TypeScript & Chất lượng Code

| Skill | Mô tả | Kích hoạt khi |
|-------|-------|---------------|
| **typescript-pro** | Hệ thống type nâng cao trong TypeScript, custom type guards, utility types, branded types, tRPC cho type safety end-to-end. Monorepo setup, conditional/mapped types, discriminated unions. | TypeScript generics, conditional types, mapped types, tRPC, monorepo |
| **typescript-react-reviewer** | Code reviewer chuyên gia cho TypeScript + React 19. Phát hiện anti-pattern, đánh giá state management, nhận diện code smell, kiểm tra TypeScript type safety. | code review, PR review, React architecture, useEffect abuse, type safety |

# Document Skills

Thư mục `document-skills/` chứa các skill Anthropic phát triển để giúp Claude tạo các định dạng tài liệu:

- **docx** - Tạo, chỉnh sửa, phân tích tài liệu Word với tracked changes, comments, bảo toàn định dạng, và trích xuất văn bản
- **pdf** - Thao tác PDF toàn diện: trích xuất text/table, tạo mới, merge/split, xử lý form
- **pptx** - Tạo, chỉnh sửa, phân tích bài trình bày PowerPoint với layouts, templates, charts, và tự động tạo slide
- **xlsx** - Tạo, chỉnh sửa, phân tích bảng tính Excel với công thức, định dạng, phân tích dữ liệu, và trực quan hóa

**Lưu ý quan trọng:** Các document skill này là ảnh chụp tại thời điểm và không được bảo trì cập nhật. Chúng chủ yếu dùng làm tài liệu tham khảo.

# Sử dụng trong Claude Code, Claude.ai, và API

## Claude Code
Đăng ký repository này như Claude Code Plugin marketplace:
```
/plugin marketplace add anthropics/skills
```

## Claude.ai
Các skill mẫu này có sẵn cho gói trả phí trong Claude.ai. Xem [Sử dụng Skills trong Claude](https://support.claude.com/en/articles/12512180-using-skills-in-claude#h_a4222fa77b).

## Claude API
Sử dụng Anthropic's pre-built skills và tải lên skill tùy chỉnh qua [Skills API Quickstart](https://docs.claude.com/en/api/skills-guide#creating-a-skill).

# Tạo Skill cơ bản

Skills rất đơn giản để tạo — chỉ cần một thư mục với file `SKILL.md`:

```markdown
---
name: my-skill-name
description: Mô tả rõ ràng về skill này làm gì và khi nào sử dụng
---

# Tên Skill Của Bạn

[Hướng dẫn mà Claude sẽ theo khi skill này được kích hoạt]

## Ví dụ
- Ví dụ sử dụng 1
- Ví dụ sử dụng 2

## Nguyên tắc
- Nguyên tắc 1
- Nguyên tắc 2
```

Các trường frontmatter bắt buộc:
- `name` - Định danh duy nhất (chữ thường, gạch nối thay khoảng trắng)
- `description` - Mô tả skill làm gì và khi nào sử dụng

Chi tiết thêm tại [Cách tạo skill tùy chỉnh](https://support.claude.com/en/articles/12512198-creating-custom-skills).

# Skills từ đối tác

Skills là cách tuyệt vời để dạy Claude sử dụng tốt hơn các phần mềm cụ thể. Khi chúng tôi thấy các skill mẫu tuyệt vời từ đối tác, chúng tôi có thể giới thiệu chúng ở đây:

- **Notion** - [Notion Skills cho Claude](https://www.notion.so/notiondevs/Notion-Skills-for-Claude-28da4445d27180c7af1df7d8615723d0)