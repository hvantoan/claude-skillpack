# Vertical Slice Architecture — Detailed Conventions

## Folder Structure Rules

### Feature Folder Naming
- Pattern: `Features/{Domain}/{Action}/`
- Domain = business area (Partners, Users, Orders, Transactions)
- Action = verb phrase (CreateTransaction, GetProfile, UpdateSettings)
- One folder per use case — co-locate endpoint, request, validator, handler

### Cross-Cutting Concerns Placement
| Concern | Location | Example |
|---------|----------|---------|
| Auth handlers | `Infrastructure/Auth/` | `HmacAuthenticationHandler.cs` |
| Queue abstractions | `Infrastructure/Messaging/` | `IMessageQueueService.cs` |
| Queue implementations | `Infrastructure/Messaging/` | `RabbitMqMessageQueueService.cs` |
| External API clients | `Shared/Contracts/` | `IPartnerClient.cs` |
| Endpoint discovery | `Shared/Extensions/` | `EndpointExtensions.cs` |
| Middleware | `Shared/Middleware/` | `GlobalExceptionHandlerMiddleware.cs` |

### What NOT to Put in Shared
- Business logic — belongs in feature slices
- Validation rules — belong with their feature
- DTOs shared between features — duplicate per slice until Rule of Three
- Service classes that orchestrate multiple features — keep orchestration in endpoint handler

## IEndpoint Interface Rules

### Required Implementation
Every endpoint MUST implement `IEndpoint`:
```csharp
public interface IEndpoint {
    void Map(IEndpointRouteBuilder app);
}
```

### Handler Signature
- MUST be `public static` for direct testability
- Inject dependencies via method parameters (DI resolves them)
- Return `Task<IResult>` for async, `IResult` for sync

### Route Convention
- Pattern: `/api/v1/{domain}/{action}` (kebab-case)
- HTTP methods: `MapGet` for queries, `MapPost` for commands
- Always call `.RequireAuthorization()` unless explicitly public

### Validation Flow
1. Inject `IValidator<TRequest>` as method parameter
2. Call `await validator.ValidateAsync(request)`
3. Return `Results.BadRequest(...)` if invalid
4. Never throw validation exceptions from handler

## Dependency Injection Rules

### Service Registration Order (Program.cs)
1. FluentValidation — `AddValidatorsFromAssemblyContaining<Program>()`
2. HTTP clients (Refit) — `AddRefitClient<T>()` with resilience
3. Middleware — `AddTransient<T>()`
4. Infrastructure — `AddSingleton<T>()` for stateful, `AddTransient<T>()` for stateless
5. Auth — `AddAuthentication()` then `AddAuthorization()`

### Double-Registration Pattern
When a service needs both `IHostedService` and DI resolution:
```csharp
builder.Services.AddSingleton<RabbitMqMessageQueueService>();
builder.Services.AddSingleton<IMessageQueueService>(sp => sp.GetRequiredService<RabbitMqMessageQueueService>());
builder.Services.AddHostedService(sp => sp.GetRequiredService<RabbitMqMessageQueueService>());
```

## Feature Slice Checklist

When adding a new feature slice, verify:
- [ ] Folder `Features/{Domain}/{Action}/` exists
- [ ] `{Action}Endpoint.cs` implements `IEndpoint`
- [ ] Handler is `public static`
- [ ] `{Action}Request.cs` has request DTO (record or class)
- [ ] `{Action}Validator.cs` extends `AbstractValidator<TRequest>`
- [ ] No business logic in shared/infrastructure — only in feature slice
- [ ] Route follows `/api/v1/{domain}/{action}` pattern
- [ ] Authorization is explicitly configured (`.RequireAuthorization()` or `[AllowAnonymous]`)