# Architectural Decisions — FastEndpoints, Shared Behaviors, Response Types, Scaling

## FastEndpoints vs MediatR

| Aspect | FastEndpoints | MediatR |
|--------|--------------|---------|
| Files per feature | Endpoint + Request + Response + Validator | Command + Handler + Validator + Controller + registration |
| Control flow | Direct, traceable (F12 works) | Indirect (dispatched via mediator) |
| Cross-cutting | Pre/Post-processors + Groups | IPipelineBehavior |
| Validation | Built-in FluentValidation integration | Manual wiring |
| Swagger | Built-in Summary/Description support | Extra config |
| Event bus | Built-in in-process event bus | INotification |
| Dependency | Open-source, active | Commercial since 2024 |

Use MediatR only for: true CQRS with separate read/write models, legacy brownfield projects, or complex pipeline ordering requiring centralized behavior chains.

## Shared Behaviors — Groups & Processors

**Core Principle:** Behavior ≠ Model. Share behaviors via Groups/processors; keep models separate per endpoint.

### Route Groups — Shared Behavior Container

```csharp
public class OrderGroup : Group {
    public OrderGroup() {
        Configure("orders", ep => {
            ep.Policies("PartnerOnly");
            ep.Description(x => x.WithTags("Orders"));
        });
    }
}
```

### Processor Attachment Options

```csharp
// 1. Global (all endpoints) — Program.cs configurator
app.UseFastEndpoints(config => {
    config.Endpoints.Configurator = ep => {
        ep.PreProcessor<RequestLoggingProcessor<object>>(Order.Before);
    };
});

// 2. Group-level — shared behavior for domain endpoints
public class OrderGroup : Group {
    public OrderGroup() {
        Configure("orders", ep => {
            ep.PreProcessor<OrderValidationProcessor>();
        });
    }
}

// 3. Endpoint-specific
public override void Configure() {
    PreProcessor<IdempotencyCheckProcessor<CreateOrderRequest>>();
    PostProcessor<AuditLogProcessor<CreateOrderRequest, Result<OrderDto>>>();
}
```

### Shared vs Separate Models

| Scenario | Model | Behavior |
|----------|-------|----------|
| 2 endpoints, different actions | Separate DTO per endpoint | Shared via Group |
| Same business logic | Domain entity (Tier 2) | Shared via Group |
| Cross-cutting (logging, auth) | N/A | Shared via global processors |

## Result<T> Envelope

```csharp
public record Result<T> {
    public bool Success { get; init; }
    public T? Data { get; init; }
    public string? Message { get; init; }
    public string[]? Errors { get; init; }

    public static Result<T> Ok(T data) => new() { Success = true, Data = data };
    public static Result<T> Fail(string message, string[]? errors = null) =>
        new() { Success = false, Message = message, Errors = errors };
}

public record PagedData<T>(List<T> Items, int TotalCount, int Page, int PageSize);
```

### Usage Patterns

```csharp
// Success
await SendOkAsync(Result<OrderDto>.Ok(orderDto), ct);
await SendCreatedAsync($"/api/v1/orders/{order.Id}", Result<OrderDto>.Ok(orderDto), ct);

// Error
await SendAsync(Result<OrderDto>.Fail("Not found"), 404, ct);

// Paged
await SendOkAsync(Result<PagedData<OrderDto>>.Ok(pagedData), ct);

// Override for special cases (file downloads, etc.)
public class DownloadReportEndpoint : Endpoint<DownloadReportRequest, FileResult> { ... }
```

### Setup (Program.cs)

```csharp
builder.Services.ConfigureHttpJsonOptions(o =>
    o.SerializerOptions.DefaultIgnoreCondition = JsonIgnoreCondition.WhenWritingNull);

app.UseFastEndpoints(config => {
    config.Errors.ResponseBuilder = (failures, ctx) =>
        Result<object>.Fail("Validation failed", failures.Select(f => f.ErrorMessage).ToArray());
});
```

### Factory Method Rules

- Always use `Result<T>.Ok(data)` — never `new Result<T> { Success = true, ... }`
- Always use `Result<T>.Fail(message, errors)` — never `new Result<T> { Success = false, ... }`
- Architecture test: grep for `new Result<` outside of `Result.cs` → violation

## Cross-Cutting Concerns

### Global Exception Handling (Middleware)

```csharp
public class GlobalExceptionHandlerMiddleware {
    private readonly RequestDelegate _next;
    private readonly ILogger<GlobalExceptionHandlerMiddleware> _logger;

    public async Task InvokeAsync(HttpContext context) {
        try {
            await _next(context);
        } catch (DomainException ex) {
            context.Response.StatusCode = 400;
            await context.Response.WriteAsJsonAsync(Result<object>.Fail(ex.Message));
        } catch (Exception ex) {
            _logger.LogError(ex, "Unhandled exception");
            context.Response.StatusCode = 500;
            await context.Response.WriteAsJsonAsync(Result<object>.Fail("An unexpected error occurred"));
        }
    }
}
```

### Unit of Work Pattern

```csharp
public override async Task HandleAsync(CreateOrderRequest req, CancellationToken ct) {
    await using var transaction = await Db.Database.BeginTransactionAsync(ct);
    try {
        var order = Order.Create(req.CustomerId, req.Items);
        Db.Orders.Add(order);
        await Db.SaveChangesAsync(ct);
        await transaction.CommitAsync(ct);
        await SendCreatedAsync($"/api/v1/orders/{order.Id}", Result<Guid>.Ok(order.Id));
    } catch {
        await transaction.RollbackAsync(ct);
        throw;
    }
}
```

### Authorization Policies Per Feature

```csharp
builder.Services.AddAuthorizationBuilder()
    .AddPolicy("PartnerOnly", policy =>
        policy.Requirements.Add(new HmacRequirement()));

// In endpoint Configure()
Policies("PartnerOnly");
```

## Folder Scaling

- <20 features: single `Features/` folder
- 20-50: sub-domain grouping (`Features/{Domain}/{SubDomain}/{Action}/`)
- 50-200: consider separate `MyApp.Domain` project
- 200+: multi-project solution with `Contracts` project for cross-boundary DTOs

Only split when domain complexity or team boundaries justify it.