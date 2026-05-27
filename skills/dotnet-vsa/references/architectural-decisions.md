# Architectural Decisions — MediatR, Cross-Cutting Concerns, Response Types, Scaling

## MediatR vs Minimal API (Decision Guide)

### Minimal API + IEndpoint (Recommended for this skill)

| Aspect | Minimal API + IEndpoint | MediatR |
|--------|----------------------|---------|
| **Files per feature** | 1 endpoint + 1 request + 1 validator | 1 command + 1 handler + 1 validator + 1 controller endpoint + registration |
| **Control flow** | Direct, traceable (F12 works) | Indirect (dispatched via mediator) |
| **Cross-cutting** | Middleware + endpoint filters | IPipelineBehavior |
| **Testability** | Static handler method, no HTTP host | Handler class, no HTTP host |
| **Boilerplate** | Low | High ceremony for simple ops |
| **Dependency** | None (built-in) | External package (commercial since 2024) |

### When to Use MediatR Instead

- **True CQRS** with separate read/write models and different databases
- **Complex pipeline behaviors** that benefit from centralized ordering (validation → auth → logging → handler)
- **Event-driven architecture** with in-process events (INotification)
- **Multiple handlers** for the same request type (rare, usually a design smell)

### When Minimal API is Better

- Standard CRUD APIs (most cases)
- Teams that value explicit control flow over abstraction
- Projects that want zero external dependency for dispatch
- When you want F12/Go-to-Definition to actually work

### Cross-Cutting Concerns Without MediatR

Replace `IPipelineBehavior` with:

1. **Middleware** — for all requests (exception handling, logging)
2. **Endpoint Filters** (.NET 8+) — for specific route groups

```csharp
// Endpoint filter for validation + logging
public class ValidationFilter<TRequest> : IEndpointFilter {
    public async ValueTask<object?> InvokeAsync(
        EndpointFilterInvocationContext ctx,
        EndpointFilterDelegate next) {
        var request = ctx.Arguments.OfType<TRequest>().First();
        var validator = ctx.HttpContext.RequestServices
            .GetRequiredService<IValidator<TRequest>>();
        var result = await validator.ValidateAsync(request);
        if (!result.IsValid)
            return Results.BadRequest(new { success = false, errors = result.Errors.Select(e => e.ErrorMessage) });
        return await next(ctx);
    }
}

// Registration
app.MapPost("/api/v1/transactions", Handle)
   .AddEndpointFilter<ValidationFilter<CreateTransactionRequest>>();
```

3. **Native DI Decorators** — replace pipeline behaviors with typed decorators

```csharp
// Using Scrutor or manual decorator registration
builder.Services.AddTransient<IOrderService>(sp => {
    var inner = new OrderService(sp.GetRequiredService<AppDbContext>());
    return new LoggingOrderServiceDecorator(inner, sp.GetRequiredService<ILogger<LoggingOrderServiceDecorator>>());
});
```

## Response Type Safety

### Current: Anonymous Objects (Simple but Untyped)
```csharp
return Results.Ok(new { success = true, data = order });
return Results.BadRequest(new { success = false, message = "Invalid" });
```
- ✅ Fast to write, no extra types
- ❌ No Swagger schema, no compile-time shape guarantee

### Recommended: Typed Results (.NET 9+)
```csharp
// Define result types
public record SuccessResponse<T>(bool Success, T Data);
public record ErrorResponse(bool Success, string Message, string[]? Errors = null);

// Use in endpoints
public static Results<Accepted<SuccessResponse<string>>, BadRequest<ErrorResponse>> Handle(...) {
    if (!validation.IsValid)
        return TypedResults.BadRequest(new ErrorResponse(false, "Validation failed", errors));
    return TypedResults.Accepted(null, new SuccessResponse<string>("Transaction queued"));
}
```
- ✅ Swagger schema auto-generated
- ✅ Compile-time return type checking
- ✅ `TypedResults` avoids reflection in minimal APIs
- ❌ More types to define

### Recommendation
- **New projects**: Use `TypedResults` + result records from start
- **Existing projects**: Migrate incrementally, start with endpoints that return complex shapes

## Cross-Cutting Concerns Patterns

### Global Exception Handling (Already in skill)
- `GlobalExceptionHandlerMiddleware` catches all unhandled exceptions
- Maps exception types to HTTP status codes

### Request/Response Logging
```csharp
public class RequestLoggingMiddleware {
    private readonly RequestDelegate _next;
    private readonly ILogger<RequestLoggingMiddleware> _logger;

    public async Task InvokeAsync(HttpContext context) {
        var sw = Stopwatch.StartNew();
        try {
            await _next(context);
        } finally {
            sw.Stop();
            _logger.LogInformation("{Method} {Path} → {StatusCode} ({ElapsedMs}ms)",
                context.Request.Method, context.Request.Path,
                context.Response.StatusCode, sw.ElapsedMilliseconds);
        }
    }
}
```

### Unit of Work Pattern
```csharp
// For multi-step handlers that need transactional consistency
public static async Task<IResult> Handle(
    CreateOrderRequest request,
    AppDbContext db) {
    await using var transaction = await db.Database.BeginTransactionAsync();
    try {
        // Step 1: Create order
        // Step 2: Reserve inventory
        // Step 3: Queue notification
        await db.SaveChangesAsync();
        await transaction.CommitAsync();
        return Results.Created(...);
    } catch {
        await transaction.RollbackAsync();
        throw;
    }
}
```

### Authorization Policies Per Feature
```csharp
// In Program.cs or feature-specific registration
builder.Services.AddAuthorizationBuilder()
    .AddPolicy("PartnerOnly", policy =>
        policy.Requirements.Add(new HmacRequirement()));

// In endpoint
app.MapPost("/api/v1/partner/transactions", Handle)
   .RequireAuthorization("PartnerOnly");
```

## Folder Scaling

### Small to Medium (<50 Features)
```
Features/
├── Partners/
│   ├── CreatePartner/
│   │   ├── CreatePartnerEndpoint.cs
│   │   ├── CreatePartnerRequest.cs
│   │   └── CreatePartnerValidator.cs
│   └── VerifyPartner/
└── Transactions/
    └── CreateTransaction/
```

### Medium to Large (50-200 Features) — Sub-Domains
```
Features/
├── Orders/
│   ├── CreateOrder/
│   ├── Fulfillment/
│   │   ├── ShipOrder/
│   │   └── CancelShipment/
│   └── Reports/
│       └── GetOrderSummary/
└── Payments/
    ├── ProcessPayment/
    └── RefundPayment/
```

### Large / Multi-Team (200+ Features) — Separate Projects
```
src/
├── MyApp.Api/              ← endpoints, DI
├── MyApp.Domain/           ← entities, value objects, domain events
├── MyApp.Contracts/        ← shared DTOs for external consumers
├── MyApp.Infrastructure/   ← EF Core, messaging, external clients
└── MyApp.Tests/
```
Only split when domain complexity or team boundaries justify it.

### Scaling Checklist

- [ ] <20 features: single `Features/` folder is fine
- [ ] 20-50 features: use sub-domain grouping (`Features/{Domain}/{SubDomain}/{Action}/`)
- [ ] 50-200 features: consider separate `MyApp.Domain` project
- [ ] 200+ features: multi-project solution with `Contracts` project for cross-boundary DTOs