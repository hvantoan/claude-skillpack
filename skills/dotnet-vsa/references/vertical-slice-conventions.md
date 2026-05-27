# Vertical Slice Architecture — FastEndpoints Conventions

## Folder Structure Rules

### Feature Folder Naming
- Pattern: `Features/{Domain}/{Action}/`
- Domain = business area (Partners, Users, Orders, Transactions)
- Action = verb phrase (CreateTransaction, GetProfile, UpdateSettings)
- One folder per use case — co-locate endpoint, request, response, validator

### Cross-Cutting Concerns Placement

| Concern | Location | Example |
|---------|----------|---------|
| Route groups | `Shared/Groups/` | `OrderGroup.cs`, `PartnerGroup.cs` |
| Pre/Post-processors | `Shared/Processors/` | `RequestLoggingProcessor.cs` |
| Auth handlers | `Infrastructure/Auth/` | `HmacAuthenticationHandler.cs` |
| Queue abstractions | `Infrastructure/Messaging/` | `IMessageQueueService.cs` |
| Queue implementations | `Infrastructure/Messaging/` | `RabbitMqMessageQueueService.cs` |
| External API clients | `Shared/Contracts/` | `IPartnerClient.cs` |
| Middleware | `Shared/Middleware/` | `GlobalExceptionHandlerMiddleware.cs` |
| Response records | `Shared/Contracts/` | `Result<T>`, `PagedData<T>` |

### What NOT to Put in Shared
- Business logic — belongs in feature slices
- Validation rules — belong with their feature
- Request/Response DTOs shared between features — duplicate per slice until Rule of Three
- Service classes that orchestrate multiple features — keep orchestration in endpoint handler

## Endpoint Convention

### Required Implementation

Every endpoint inherits from `Endpoint<TRequest, TResponse>`:

```csharp
public class CreateOrderEndpoint : Endpoint<CreateOrderRequest, Result<OrderDto>> {
    // Property injection — auto-resolved by DI
    public AppDbContext Db { get; set; } = null!;
    public IPartnerClient Client { get; set; } = null!;

    public override void Configure() {
        Post("/api/v1/orders");
        Policies("PartnerOnly");
        Summary(s => {
            s.Summary = "Create a new order";
            s.ResponseExamples[201] = Result<OrderDto>.Ok(new OrderDto(Guid.NewGuid(), "Created"));
        });
    }

    public override async Task HandleAsync(CreateOrderRequest req, CancellationToken ct) {
        var order = Order.Create(req.CustomerId, req.Items);
        Db.Orders.Add(order);
        await Db.SaveChangesAsync(ct);
        await SendCreatedAsync($"/api/v1/orders/{order.Id}",
            Result<OrderDto>.Ok(new OrderDto(order.Id, "Created")), ct);
    }
}
```

### Configure Method Rules
- Use `Post()`, `Get()`, `Put()`, `Delete()`, `Patch()` for HTTP method
- Always set `Policies()` unless endpoint is public (then use `AllowAnonymous()`)
- Use `Group<T>()` to assign to a route group
- Use `Summary()` for Swagger documentation
- Use `Description()` for additional Swagger metadata
- Use `PreProcessor<T>()` / `PostProcessor<T>()` for endpoint-specific processors
- Route pattern: relative path within group, or absolute `/api/v1/{domain}/{action}` (kebab-case)

### Handler Signature Rules
- Override `HandleAsync(TRequest req, CancellationToken ct)`
- Access DI services via property injection
- Return responses via `Send` methods
- Never throw exceptions for validation — use `AddError()` + `ThrowIfAnyErrors()`
- Throw `DomainException` for business rule violations (caught by middleware)

### Dependency Injection

FastEndpoints supports three DI methods:

```csharp
// 1. Property injection (recommended for most cases)
public class CreateOrderEndpoint : Endpoint<CreateOrderRequest, Result<OrderDto>> {
    public AppDbContext Db { get; set; } = null!;  // auto-resolved
    public ILogger<CreateOrderEndpoint> Logger { get; set; } = null!;
}

// 2. Constructor injection (when you need explicit control)
public class CreateOrderEndpoint(AppDbContext db, ILogger<CreateOrderEndpoint> logger)
    : Endpoint<CreateOrderRequest, Result<OrderDto>> {
    private readonly AppDbContext _db = db;
    private readonly ILogger _logger = logger;
}

// 3. Manual resolve (rare, for transient services)
public override async Task HandleAsync(CreateOrderRequest req, CancellationToken ct) {
    var service = Resolve<ITransientService>();
}
```

### Endpoint Types

| Type | Use When | Example |
|------|----------|---------|
| `Endpoint<TReq, TRes>` | Standard request with typed response | Create, Update |
| `Endpoint<TReq>` | No response body (or empty) | Delete |
| `EndpointWithoutRequest<TRes>` | GET with no body, typed response | Get list |
| `EndpointWithoutRequest` | Health check, ping | Health endpoint |
| `JsonRequest<TReq, TRes>` | Custom JSON serialization | Non-standard JSON |

## Route Group Convention

### Defining Groups

```csharp
// Shared/Groups/OrderGroup.cs
public class OrderGroup : Group {
    public OrderGroup() {
        Configure("orders", ep => {
            ep.Policies("PartnerOnly");
            ep.Description(x => x.WithTags("Orders"));
        });
    }
}

// Shared/Groups/AdminGroup.cs — nested group
public class AdminGroup : Group {
    public AdminGroup() {
        Configure("admin", ep => {
            ep.Policies("AdminOnly");
        });
    }
}
```

### Assigning Endpoints to Groups

```csharp
public class CreateOrderEndpoint : Endpoint<CreateOrderRequest, Result<OrderDto>> {
    public override void Configure() {
        Post("/create");              // relative to group prefix → /orders/create
        Group<OrderGroup>();
    }
}

public class GetOrderEndpoint : EndpointWithoutRequest<Result<OrderDto>> {
    public override void Configure() {
        Get("/{OrderId}");            // → /orders/{OrderId}
        Group<OrderGroup>();
        AllowAnonymous();             // override group policy
    }
}
```

## Validation Convention

### FluentValidation (Auto-Discovered)

FastEndpoints auto-discovers validators inheriting `Validator<TRequest>`:

```csharp
public class CreateOrderValidator : Validator<CreateOrderRequest> {
    public CreateOrderValidator() {
        RuleFor(x => x.CustomerId).NotEmpty();
        RuleFor(x => x.Items).NotEmpty();
        RuleFor(x => x.Currency)
            .NotEmpty()
            .Must(c => ValidCurrencies.Contains(c))
            .WithMessage("Unsupported currency");
    }
}
```

Validation runs **before** `HandleAsync()`. If validation fails, a 400 response is returned automatically and `HandleAsync` is never called.

### In-Handler Validation (Application Logic)

For business rules that need database/API calls:

```csharp
public override async Task HandleAsync(CreateUserRequest req, CancellationToken ct) {
    if (await Db.Users.AnyAsync(u => u.Email == req.Email, ct))
        AddError(r => r.Email, "Email already in use");

    var maxAge = await Settings.GetMaxAllowedAge();
    if (req.Age >= maxAge)
        AddError(r => r.Age, "Not eligible");

    ThrowIfAnyErrors(); // 400 if any errors, execution stops

    // Only reaches here if no errors
    var user = User.Create(req.Email, req.Age);
    await Db.SaveChangesAsync(ct);
    await SendOkAsync(Result<UserDto>.Ok(new UserDto(user.Id)), ct);
}
```

### Custom Error Response

```csharp
// Program.cs
app.UseFastEndpoints(config => {
    config.Errors.ResponseBuilder = (failures, ctx) => {
        return Result<object>.Fail("Validation failed", failures.Select(f => f.ErrorMessage).ToArray());
    };
});
```

## Pre/Post-Processors Convention

### When to Use

| Use Case | Mechanism |
|----------|-----------|
| Logging all requests | Global pre-processor |
| Response timing | Global post-processor |
| Tenant resolution | Global pre-processor |
| Feature-specific auth check | Group-level processor |
| Idempotency check | Endpoint-specific pre-processor |
| Audit logging | Endpoint-specific post-processor |

### Processor Patterns

```csharp
// Global processor (all endpoints)
public class RequestLoggingProcessor : IGlobalPreProcessor {
    public async Task PreProcessAsync(IPreProcessorContext ctx, CancellationToken ct) {
        // runs before every endpoint handler
    }
}

// Typed pre-processor (specific request type)
public class IdempotencyCheck<TReq> : IPreProcessor<TReq> {
    public async Task PreProcessAsync(IPreProcessorContext<TReq> ctx, CancellationToken ct) {
        // runs only for endpoints with matching TReq
    }
}

// Post-processor
public class AuditLogger<TReq, TRes> : IPostProcessor<TReq, TRes> {
    public async Task PostProcessAsync(IPostProcessorContext<TReq, TRes> ctx, CancellationToken ct) {
        // runs after every handler (success or failure)
    }
}
```

## Service Registration (Program.cs)

### Registration Order

1. FastEndpoints — `builder.Services.AddFastEndpoints()`
2. FluentValidation — `builder.Services.AddValidatorsFromAssemblyContaining<Program>()`
3. HTTP clients (Refit) — `builder.Services.AddRefitClient<T>()` with resilience
4. Processors — registered automatically by FastEndpoints
5. Infrastructure — `AddSingleton<T>()` for stateful, `AddTransient<T>()` for stateless
6. Auth — `AddAuthentication()` then `AddAuthorization()`
7. Build — `builder.Build()`
8. Pipeline — middleware, then `app.UseFastEndpoints()`

### Double-Registration Pattern

When a service needs both `IHostedService` and DI resolution:

```csharp
builder.Services.AddSingleton<RabbitMqMessageQueueService>();
builder.Services.AddSingleton<IMessageQueueService>(sp =>
    sp.GetRequiredService<RabbitMqMessageQueueService>());
builder.Services.AddHostedService(sp =>
    sp.GetRequiredService<RabbitMqMessageQueueService>());
```

## Feature Slice Checklist

When adding a new feature slice, verify:

- [ ] Folder `Features/{Domain}/{Action}/` exists
- [ ] `{Action}Endpoint.cs` inherits `Endpoint<TRequest, TResponse>`
- [ ] `{Action}Request.cs` has request DTO (record)
- [ ] `{Action}Response.cs` has response DTO (record)
- [ ] `{Action}Validator.cs` extends `Validator<TRequest>`
- [ ] `Configure()` sets HTTP method, route, and policies
- [ ] Route follows `/api/v1/{domain}/{action}` pattern (or relative within group)
- [ ] DI services injected via properties with `= null!`
- [ ] No business logic in shared/infrastructure — only in feature slice or domain entities
- [ ] Group assigned if endpoint belongs to a domain group
