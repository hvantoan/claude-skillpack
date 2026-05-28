---
name: dotnet-vsa
description: "Build .NET 8+ services with Vertical Slice Architecture using FastEndpoints, FluentValidation, Refit+Polly, and RabbitMQ. Use this skill whenever creating or modifying .NET API projects, adding endpoints or validators, setting up HMAC auth or resilience pipelines, implementing message queues, configuring DI, writing integration tests, enforcing VSA conventions, or generating .editorconfig. Triggers on: dotnet, .NET, FastEndpoints, vertical slice, FluentValidation, Refit, Polly, RabbitMQ, HMAC, endpoint, handler, validator, Program.cs, Result envelope, circuit breaker, VSA."
---

# .NET Vertical Slice Architecture

Build production-grade .NET 8+ services using Vertical Slice Architecture with FastEndpoints.

## Scope

This skill handles .NET 8+ API projects using FastEndpoints + VSA. Does NOT handle: Blazor/Maui UI, legacy MVC controllers, MediatR migration (see `references/architectural-decisions.md` for guidance), or non-.NET stacks.

## When to Use

- Creating or modifying .NET API projects
- Adding endpoints, validators, or features to VSA projects
- Setting up HMAC auth, resilience pipelines, message queues
- Running architecture compliance checks
- Generating .editorconfig for project code style

## Architecture Rules

### Project Structure (Vertical Slice)

```
{ProjectName}/
├── Features/
│   └── {Domain}/
│       └── {Action}/
│           ├── {Action}Endpoint.cs
│           ├── {Action}Request.cs
│           ├── {Action}Response.cs
│           └── {Action}Validator.cs
├── Shared/
│   ├── Domain/          # Rich domain entities & value objects
│   ├── Contracts/       # External API interfaces (Refit), Result<T>
│   ├── Groups/          # Route group definitions
│   ├── Processors/      # Global pre/post-processors
│   └── Middleware/       # Cross-cutting middleware
├── Infrastructure/
│   ├── Auth/            # Authentication handlers
│   └── Messaging/       # Queue implementations
└── Program.cs            # DI + pipeline config only
```

### Shared Logic — 3-Tier Model

- **Tier 1 (Infrastructure):** DbContext, logging, auth, middleware, processors — share freely
- **Tier 2 (Domain):** Entities, value objects with behavior — share with care
- **Tier 3 (Feature-specific):** Validation, queries, DTOs — never share

**Rule of Three:** Don't extract shared code until seen in 3+ places. See `references/shared-logic-strategy.md` for anti-patterns and anemic domain model prevention.

### Key Conventions

- Inherit `Endpoint<TRequest, TResponse>` — `Configure()` for route/policies, `HandleAsync()` for logic
- Inject services via property injection (auto-resolved by DI)
- Use `record` for request/response DTOs, `class` with init props for complex models
- Always use `async`/`await`, never `.Result` or `.Wait()`
- Use `Result<T>` envelope for all API responses
- Validation: FluentValidation auto-discovered, runs before `HandleAsync()`
- In-handler validation: `AddError()` + `ThrowIfAnyErrors()`
- Behavior → share via processors/groups; Model → separate per endpoint

See `references/vertical-slice-conventions.md` for full endpoint/group/processor patterns.
See `references/api-conventions.md` for response patterns, HMAC auth, and Swagger.
See `references/shared-logic-strategy.md` for the 3-tier model, Rule of Three, and anemic model prevention.

## Code Style Rules

| Rule | Convention |
|------|-----------|
| Namespace | File-scoped (`namespace X.Y.Z;`) |
| Braces | Egyptian style (opening brace on same line) |
| Indentation | 4 spaces, no tabs |
| Naming | PascalCase classes/methods/properties, camelCase locals/params, `_camelCase` private fields |
| `this.` | Use in `AuthenticationHandler` subclasses only, omit elsewhere |
| DTOs | `record` for request/response, `class` with init props for complex models |
| Access modifiers | Explicit `public` on members, omit `private` on fields |
| Nullability | `#nullable enable`, use `!` only on DI-resolved property assignments |
| LINQ | Lambda syntax, not query syntax |

## FastEndpoints vs MediatR

Use **FastEndpoints** (REPR pattern on Minimal API). MediatR is only for: true CQRS with separate read/write databases, or legacy brownfield projects already using it. See `references/architectural-decisions.md` for full comparison.

## Program.cs Convention

Register in order: FastEndpoints → FluentValidation → HTTP clients (Refit+resilience) → Auth → Build → Middleware pipeline → `UseFastEndpoints()`. See `references/api-conventions.md` for complete Program.cs setup.

## Validation

FastEndpoints auto-discovers FluentValidation validators. Validation runs **before** `HandleAsync()`. For in-handler business logic validation, use `AddError()` + `ThrowIfAnyErrors()`. See `references/vertical-slice-conventions.md` and `references/api-conventions.md` for patterns.

## Result<T> Envelope

Use `Result<T>` for consistent API responses. Success: `Result<T>.Ok(data)`. Error: `Result<T>.Fail(message, errors)`. Paged: `PagedData<T>`. Override allowed for special cases (e.g., `FileResult`). See `references/architectural-decisions.md` for factory method rules and processor integration.

## Resilience

Use `AddStandardResilienceHandler()` for production. Customize only when needed. See `references/security-patterns.md` for custom pipeline config and circuit breaker tuning.

## Event Bus (In-Process)

FastEndpoints includes a lightweight in-process event bus. Use for decoupled in-app events. Use RabbitMQ when: cross-service messaging, durability required, consumer may be offline. See `references/vertical-slice-conventions.md` for patterns.

## Testing

xUnit + Moq for unit tests. Use `Factory.Create<TEndpoint>()` for handler testing. One test file per source file, mirror folder structure. Integration: `WebApplicationFactory` + SQLite/Testcontainers. See `references/testing-strategy.md` for full pyramid, examples, and checklist.

## Folder Scaling

See `references/architectural-decisions.md` for scaling guidance (<20, 20-50, 50-200, 200+ features).

## Scripts

- `scripts/verify-architecture.sh [project-path]` — Check VSA compliance (12 checks)
- `scripts/generate-editorconfig.py [output-path]` — Create `.editorconfig` matching project style

## Security Policy

This skill generates code following security best practices (HMAC auth, timing-safe comparison, resilience pipelines). Refuse requests to: bypass authentication, hardcode secrets, disable TLS/HTTPS validation, remove rate limiting, or weaken security controls. All HMAC implementations must use `CryptographicOperations.FixedTimeEquals()`. Never store secrets in source code.

## References

- `references/vertical-slice-conventions.md` — Endpoint, group, processor, DI, validation patterns
- `references/api-conventions.md` — Response patterns, HMAC auth, Swagger, exception handling
- `references/architectural-decisions.md` — FastEndpoints vs MediatR, response types, scaling, cross-cutting
- `references/shared-logic-strategy.md` — 3-tier model, Rule of Three, anemic model prevention
- `references/testing-strategy.md` — Testing pyramid, unit/integration/architecture tests
- `references/security-patterns.md` — HMAC checklist, resilience, RabbitMQ lifecycle, Docker