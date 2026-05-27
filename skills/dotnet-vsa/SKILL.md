---
name: dotnet-vsa
description: Build .NET 8+ services with Vertical Slice Architecture, Minimal APIs, FluentValidation, Refit+Polly, and RabbitMQ. Use this skill when creating or modifying .NET API projects, adding endpoints, setting up authentication, configuring resilience pipelines, implementing message queues, or enforcing VSA conventions. Triggers on: dotnet, .NET, minimal API, vertical slice, FluentValidation, Refit, Polly, RabbitMQ, HMAC, endpoint, handler, validator.
---

# .NET Vertical Slice Architecture

Build production-grade .NET 8+ services using Vertical Slice Architecture.

## When to Use

- Creating new .NET API projects
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
│           ├── {Action}Endpoint.cs       # Minimal API handler
│           ├── {Action}Request.cs          # Request DTO
│           └── {Action}Validator.cs        # FluentValidation rules
├── Shared/
│   ├── Domain/                            # Rich domain entities & value objects
│   ├── Contracts/                         # External API interfaces (Refit)
│   ├── Extensions/                        # IEndpoint auto-discovery
│   └── Middleware/                        # Cross-cutting middleware
├── Infrastructure/
│   ├── Auth/                              # Authentication handlers
│   └── Messaging/                         # Queue implementations
└── Program.cs                              # DI + pipeline config only
```

### Shared Logic — 3-Tier Model

| Tier | What | Share? |
|------|------|--------|
| 1: Infrastructure | DbContext, logging, auth, middleware | ✅ Freely |
| 2: Domain | Entities, value objects with behavior | ✅ With care |
| 3: Feature-specific | Validation, queries, DTOs | ❌ Never |

**Rule of Three:** Don't extract shared code until seen in 3+ places. Two copies are tolerable. See `references/shared-logic-strategy.md` for full guide including anti-patterns and anemic domain model prevention.

### Endpoint Convention

1. Implement `IEndpoint` interface
2. `Map()` registers route, `Handle()` is `static` for testability
3. Inject validators, clients, services via method params
4. Validation → external call → queue/persist → return result

```csharp
public class CreateTransactionEndpoint : IEndpoint {
    public void Map(IEndpointRouteBuilder app) {
        app.MapPost("/api/v1/partner/transactions", Handle)
           .RequireAuthorization();
    }

    public static async Task<IResult> Handle(
        CreateTransactionRequest request,
        IValidator<CreateTransactionRequest> validator,
        IPartnerClient partnerClient,
        IMessageQueueService messageQueueService) {
        // 1. Validate
        var validation = await validator.ValidateAsync(request);
        if (!validation.IsValid)
            return Results.BadRequest(new { success = false, errors = validation.Errors.Select(e => e.ErrorMessage) });
        // 2. External call
        var isVerified = await partnerClient.VerifyPartnerAsync(request.PartnerId);
        if (!isVerified) return Results.Json(new { success = false, message = "Verification failed" }, statusCode: 502);
        // 3. Queue/persist
        await messageQueueService.PublishAsync(request);
        return Results.Accepted(null, new { success = true, message = "Transaction accepted and queued" });
    }
}
```

### Rich Domain Model — Avoid Anemic Model

Push business logic into domain objects, not handlers:

```csharp
// ❌ Anemic — logic in handler, scattered across slices
var order = new Order { Status = OrderStatus.Created }; // just a data holder

// ✅ Rich — logic in domain object, handlers orchestrate
var order = Order.Create(customerId, items); // encapsulates rules
```

See `references/shared-logic-strategy.md` for detailed patterns and checklist.

### IEndpoint Auto-Discovery

```csharp
public interface IEndpoint {
    void Map(IEndpointRouteBuilder app);
}

public static class EndpointExtensions {
    public static void MapEndpoints(this WebApplication app, Assembly assembly) {
        var endpointTypes = assembly.GetTypes()
            .Where(t => typeof(IEndpoint).IsAssignableFrom(t) && !t.IsInterface && !t.IsAbstract);
        foreach (var type in endpointTypes) {
            var endpoint = (IEndpoint)Activator.CreateInstance(type)!;
            endpoint.Map(app);
        }
    }
}
```

## Code Style Rules

| Rule | Convention |
|------|-----------|
| Namespace | File-scoped (`namespace X.Y.Z;`) |
| Braces | Egyptian style (opening brace on same line) |
| Indentation | 4 spaces, no tabs |
| Naming | PascalCase classes/methods/properties, camelCase locals/params, `_camelCase` private fields |
| `this.` | Use in `AuthenticationHandler` subclasses (disambiguate from base), omit elsewhere |
| Primary constructors | Use for DI-injected services when handler has 1-3 dependencies |
| DTOs | Use `record` for simple data, `class` with init props for complex models |
| Access modifiers | Explicit `public` on members, omit `private` on fields in primary constructors |
| Async | Always `async`/`await`, never `.Result` or `.Wait()` |
| Nullability | `#nullable enable`, use `!` only on DI-resolved services |
| LINQ | Lambda syntax (`Select(x => x.Foo)`), not query syntax |

## MediatR vs Minimal API

This skill uses **Minimal API + IEndpoint** (recommended for most APIs). Use MediatR only for true CQRS with separate read/write databases. See `references/architectural-decisions.md` for full comparison and migration guidance.

Cross-cutting concerns use **middleware + endpoint filters** (not MediatR pipeline behaviors):

```csharp
app.MapPost("/api/v1/transactions", Handle)
   .AddEndpointFilter<ValidationFilter<CreateTransactionRequest>>();
```

## Program.cs Convention

```csharp
// 1. Usings (alphabetical, System first)
// 2. Create builder
var builder = WebApplication.CreateBuilder(args);
// 3. Register services (group by concern)
builder.Services.AddValidatorsFromAssemblyContaining<Program>();
builder.Services.AddRefitClient<IPartnerClient>()...;
builder.Services.AddAuthentication("Hmac")...;
builder.Services.AddAuthorization();
// 4. Build app
var app = builder.Build();
// 5. Configure pipeline (order matters!)
app.UseMiddleware<GlobalExceptionHandlerMiddleware>();
app.UseHttpsRedirection();
app.UseAuthentication();
app.UseAuthorization();
app.MapEndpoints(typeof(Program).Assembly);
app.Run();
```

## Response Type Safety

For .NET 9+ projects, prefer `TypedResults` + result records for Swagger schema generation:

```csharp
public record SuccessResponse<T>(bool Success, T Data);
public record ErrorResponse(bool Success, string Message, string[]? Errors = null);

public static Results<Accepted<SuccessResponse<string>>, BadRequest<ErrorResponse>> Handle(...) {
    if (!validation.IsValid)
        return TypedResults.BadRequest(new ErrorResponse(false, "Validation failed", errors));
    return TypedResults.Accepted(null, new SuccessResponse<string>("Queued"));
}
```

See `references/architectural-decisions.md` for full TypedResults migration guide.

## Resilience Convention

Use `AddStandardResilienceHandler()` for production. If customizing:

```csharp
.AddResilienceHandler("name", pipeline => {
    pipeline.AddTotalRequestTimeout(TimeSpan.FromSeconds(60));
    pipeline.AddRetry(new HttpRetryStrategyOptions {
        MaxRetryAttempts = 3, Delay = TimeSpan.FromMilliseconds(500),
        BackoffType = DelayBackoffType.Exponential, UseJitter = true
    });
    pipeline.AddCircuitBreaker(new HttpCircuitBreakerStrategyOptions {
        FailureRatio = 0.5, MinimumThroughput = 10,
        SamplingDuration = TimeSpan.FromSeconds(30), BreakDuration = TimeSpan.FromSeconds(15)
    });
    pipeline.AddTimeout(TimeSpan.FromSeconds(30));
});
```

## Testing Convention

- xUnit + Moq, no external dependencies for unit tests
- Test handler as static method directly (no HTTP host needed)
- One test file per source file, mirror folder structure in test project
- Test naming: `MethodName_Scenario_ExpectedBehavior`
- Use `FakeTimeProvider` instead of mocking `DateTime`
- Integration tests: `WebApplicationFactory` + SQLite in-memory (or Testcontainers for production-equivalent)
- Architecture tests enforce `IEndpoint` implementation and `Handle` is static

See `references/testing-strategy.md` for full testing pyramid, examples, and checklist.

## Folder Scaling

- **<20 features:** single `Features/` folder is fine
- **20-50 features:** sub-domain grouping (`Features/{Domain}/{SubDomain}/{Action}/`)
- **50-200 features:** consider separate `MyApp.Domain` project
- **200+ features:** multi-project solution with `Contracts` project

See `references/architectural-decisions.md` for full scaling guidance.

## Architecture Verification

Run `scripts/verify-architecture.sh` to check project compliance. See `references/vertical-slice-conventions.md` for detailed rules.

## Generate .editorconfig

Run `scripts/generate-editorconfig.py` to create `.editorconfig` matching project style. See `references/code-style-reference.md` for full rules.