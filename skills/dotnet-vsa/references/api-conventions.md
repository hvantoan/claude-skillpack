# Minimal API & Authentication Conventions

## Minimal API Response Patterns

### Success Responses
```csharp
// 200 OK
return Results.Ok(new { success = true, data = result });

// 201 Created
return Results.Created($"/api/v1/resource/{result.Id}", new { success = true, data = result });

// 202 Accepted (async processing)
return Results.Accepted(null, new { success = true, message = "Request accepted and queued" });
```

### Error Responses
```csharp
// 400 Bad Request (validation)
return Results.BadRequest(new { success = false, message = "Validation failed", errors = ... });

// 401 Unauthorized
return Results.Json(new { success = false, message = "..." }, statusCode: 401);

// 404 Not Found
return Results.NotFound(new { success = false, message = "Resource not found" });

// 502 Bad Gateway (upstream failure)
return Results.Json(new { success = false, message = "Upstream verification failed" }, statusCode: 502);

// 503 Service Unavailable (infra failure)
return Results.Json(new { success = false, message = "Service temporarily unavailable" }, statusCode: 503);
```

### Response DTO Convention
All responses use anonymous objects with consistent shape:
```csharp
new { success = true/false, message?, data?, errors? }
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
public class CreateTransactionValidator : AbstractValidator<CreateTransactionRequest> {
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
- Static `ValidCurrencies` array for enum-like validation
- Custom messages via `.WithMessage()` when default is unclear
- Register via `AddValidatorsFromAssemblyContaining<Program>()`

## Global Exception Handler Convention

### Exception Mapping
```csharp
var (statusCode, message, errors) = ex switch {
    ValidationException ve => (400, "Validation failed", ve.Errors.Select(e => e.ErrorMessage).ToArray()),
    TimeoutException => (504, "Request timed out", Array.Empty<string>()),
    UnauthorizedAccessException => (401, "Unauthorized", Array.Empty<string>()),
    _ => (500, "An unexpected error occurred", Array.Empty<string>())
};
```

### Rules
- Never leak stack traces to clients
- Always log unhandled exceptions
- Use `application/json` content type
- Consider RFC 7807 ProblemDetails for standardization