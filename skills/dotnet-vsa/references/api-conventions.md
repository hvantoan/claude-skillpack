# FastEndpoints API & Authentication Conventions

## Response Patterns

### Result<T> Envelope

All endpoints use `Result<T>` as the standard response envelope:

```csharp
// Shared/Contracts/Result.cs
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

### Success Responses

```csharp
// 200 OK
await SendOkAsync(Result<OrderDto>.Ok(orderDto), ct);

// 201 Created
await SendCreatedAsync($"/api/v1/orders/{order.Id}", Result<OrderDto>.Ok(orderDto), ct);

// 202 Accepted (async processing)
await SendAcceptedAsync(Result<string>.Ok("Transaction queued"), ct);

// Paged
await SendOkAsync(Result<PagedData<OrderDto>>.Ok(pagedData), ct);
```

### Error Responses

```csharp
// 400 Bad Request (from validation — automatic via Error.ResponseBuilder)
// FastEndpoints returns 400 when FluentValidation fails, shape = Result<object>.Fail(...)

// 400 Bad Request (manual — in-handler)
AddError(r => r.Field, "Error message");
ThrowIfAnyErrors(); // sends 400

// 401 Unauthorized
await SendUnauthorizedAsync(ct);

// 403 Forbidden
await SendForbiddenAsync(ct);

// 404 Not Found
await SendNotFoundAsync(ct);

// Custom error (502, 503, etc.)
await SendAsync(Result<OrderDto>.Fail("Upstream verification failed"), 502, ct);
await SendAsync(Result<OrderDto>.Fail("Service unavailable"), 503, ct);
```

### JSON Output (null fields omitted)

```json
// Success: {"success": true, "data": {"id": "...", "name": "..."}}
// Error:   {"success": false, "message": "Validation failed", "errors": ["Amount required"]}
// Paged:  {"success": true, "data": {"items": [...], "totalCount": 42, "page": 1, "pageSize": 20}}
```

Setup null-omit in `Program.cs`:
```csharp
builder.Services.ConfigureHttpJsonOptions(o =>
    o.SerializerOptions.DefaultIgnoreCondition = JsonIgnoreCondition.WhenWritingNull);
```

## HMAC Authentication Pattern

### Signature Algorithm

```
bodyHash  = SHA256(rawBody).toLowerHex()
signedStr = "{unixTimestamp}:{bodyHash}"
signature = Base64(HMAC-SHA256(partnerSecret, signedStr))
```

### Required Headers

```
X-Timestamp: <unix timestamp UTC>
X-Signature: <base64 HMAC-SHA256>
```

### Handler Implementation Checklist

- [ ] Enable request buffering: `Request.EnableBuffering()`
- [ ] Read body, then reset: `Request.Body.Position = 0`
- [ ] Use `CryptographicOperations.FixedTimeEquals()` for signature comparison
- [ ] Return `AuthenticateResult.NoResult()` for missing signature (allows anonymous fallback)
- [ ] Return `AuthenticateResult.Fail(reason)` for invalid requests
- [ ] Extract partnerId from body to look up secret
- [ ] Validate timestamp freshness (±5 minutes recommended)
- [ ] Consider nonce for replay protection

### Secret Configuration

```json
{
  "Security": {
    "PartnerSecrets": {
      "partner-01": "secret-key-here"
    }
  }
}
```

Docker env override: `Security__PartnerSecrets__partner-01=docker-secret`

## FluentValidation Convention

### Validator Structure

```csharp
public class CreateTransactionValidator : Validator<CreateTransactionRequest> {
    private static readonly string[] ValidCurrencies = ["USD", "EUR", "GBP", "VND", "JPY", "SGD"];

    public CreateTransactionValidator() {
        RuleFor(x => x.PartnerId).NotEmpty();
        RuleFor(x => x.TransactionReference).NotEmpty();
        RuleFor(x => x.Amount).GreaterThan(0);
        RuleFor(x => x.Currency)
            .NotEmpty()
            .Must(c => ValidCurrencies.Contains(c))
            .WithMessage("Currency must be one of: USD, EUR, GBP, VND, JPY, SGD");
        RuleFor(x => x.Timestamp).NotEqual(default(DateTime));
    }
}
```

### Rules

- One rule per line, chained with `.Must()`, `.WithMessage()`
- Static arrays for enum-like validation (e.g., `ValidCurrencies`)
- Custom messages via `.WithMessage()` when default is unclear
- Auto-registered via `AddFastEndpoints()` + `AddValidatorsFromAssemblyContaining<Program>()`
- Validation executes before `HandleAsync()` automatically

### In-Handler Validation

```csharp
// For business rules requiring DB/API access
public override async Task HandleAsync(CreateUserRequest req, CancellationToken ct) {
    if (await Db.Users.AnyAsync(u => u.Email == req.Email, ct))
        AddError(r => r.Email, "Email already registered");

    ThrowIfAnyErrors();
    // continues only if no errors
}
```

## Global Exception Handler Convention

### Exception Mapping

```csharp
var (statusCode, message) = ex switch {
    DomainException de => (400, de.Message),
    ValidationException ve => (400, "Validation failed"),
    TimeoutException => (504, "Request timed out"),
    UnauthorizedAccessException => (401, "Unauthorized"),
    _ => (500, "An unexpected error occurred")
};
```

### Rules

- Never leak stack traces to clients
- Always log unhandled exceptions
- Use `application/json` content type
- Consider RFC 7807 ProblemDetails for standardization
- FastEndpoints validation errors bypass this middleware (handled by framework)

## Swagger Integration

FastEndpoints auto-generates Swagger docs. Enhance with:

```csharp
public override void Configure() {
    Post("/api/v1/orders");
    Summary(s => {
        s.Summary = "Create a new order";
        s.Description = "Creates an order and queues it for processing.";
        s.ExampleRequest = new CreateOrderRequest {
            CustomerId = Guid.NewGuid(),
            Items = [new OrderItemDto { ProductId = "SKU-001", Quantity = 2 }]
        };
        s.ResponseExamples[201] = Result<OrderDto>.Ok(new OrderDto(Guid.NewGuid(), "Created"));
        s.ResponseExamples[400] = Result<object>.Fail("Validation failed", ["Items required"]);
        s.Responses[201] = "Order created";
        s.Responses[400] = "Validation failed";
        s.Responses[401] = "Unauthorized";
    });
    Description(b => b.Produces(403));
}
```
