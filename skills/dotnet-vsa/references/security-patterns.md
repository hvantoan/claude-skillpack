# Security & Resilience Patterns

## HMAC Security Checklist

### Required (P0)
- [ ] `CryptographicOperations.FixedTimeEquals()` for signature comparison (prevent timing attacks)
- [ ] Timestamp validation — reject requests older than ±5 minutes
- [ ] Partner secret stored in config/env vars, never in source code
- [ ] Request body buffering + position reset for re-reading
- [ ] HTTPS enforcement in production (`UseHsts()`)

### Recommended (P1)
- [ ] Nonce tracking via `IMemoryCache` with sliding expiration for replay protection
- [ ] Sign HTTP method + path in addition to body hash: `{METHOD}:{PATH}:{timestamp}:{bodyHash}`
- [ ] Multiple active keys per partner for key rotation
- [ ] Rate limiting per partner (`AddRateLimiter()`)

### Development Tools
- [ ] `GenerateSignature` endpoint for test/dev signature computation
- [ ] Gate behind `IHostEnvironment.IsDevelopment()` or `[AllowAnonymous]` + rate limit

## Resilience Pipeline

### Production-Ready (Recommended)
```csharp
builder.Services.AddRefitClient<IPartnerClient>()
    .ConfigureHttpClient(c => c.BaseAddress = new Uri(config["ExternalApi:BaseUrl"]!))
    .AddStandardResilienceHandler();
```
Single line, 5-strategy pipeline: total timeout, retry, rate limiter, circuit breaker, attempt timeout.

### Custom Pipeline (When Needed)
```csharp
.AddResilienceHandler("name", pipeline => {
    pipeline.AddTotalRequestTimeout(TimeSpan.FromSeconds(60));
    pipeline.AddRetry(new HttpRetryStrategyOptions {
        MaxRetryAttempts = 3,
        Delay = TimeSpan.FromMilliseconds(500),
        BackoffType = DelayBackoffType.Exponential,
        UseJitter = true
    });
    pipeline.AddCircuitBreaker(new HttpCircuitBreakerStrategyOptions {
        FailureRatio = 0.5,
        MinimumThroughput = 10,
        SamplingDuration = TimeSpan.FromSeconds(30),
        BreakDuration = TimeSpan.FromSeconds(15)
    });
    pipeline.AddTimeout(TimeSpan.FromSeconds(30));
});
```

### Circuit Breaker Tuning
| Setting | Recommended | Why |
|---------|-----------|-----|
| `FailureRatio` | 0.5+ | Avoid false positives on low traffic |
| `MinimumThroughput` | 10 | Statistically reliable detection |
| `SamplingDuration` | 30s | Fast detection without overreaction |
| `BreakDuration` | 15s | Quick recovery once downstream stabilizes |

## RabbitMQ Lifecycle

### Connection Management
- Create connection in `IHostedService.StartAsync` — singleton lifecycle
- Enable auto-recovery: `AutomaticRecoveryEnabled = true`, `TopologyRecoveryEnabled = true`
- Set `NetworkRecoveryInterval = TimeSpan.FromSeconds(5)`
- Create channel per publish operation, dispose immediately (`await using var channel`)
- Null-check connection before use — throw meaningful exception if unavailable

### Double-Registration Pattern
```csharp
builder.Services.AddSingleton<RabbitMqMessageQueueService>();
builder.Services.AddSingleton<IMessageQueueService>(sp =>
    sp.GetRequiredService<RabbitMqMessageQueueService>());
builder.Services.AddHostedService(sp =>
    sp.GetRequiredService<RabbitMqMessageQueueService>());
```
Same instance registered 3 ways: as concrete type, as interface, as hosted service.

### Configuration
```json
{
  "RabbitMQ": {
    "Host": "localhost",
    "Port": 5672,
    "Username": "guest",
    "Password": "guest",
    "QueueName": "partner-transactions"
  }
}
```

## Docker Compose Convention

```yaml
services:
  rabbitmq:
    image: rabbitmq:3-management
    ports: ["5672:5672", "15672:15672"]

  {project-name}:
    build:
      context: .
      dockerfile: {ProjectName}/Dockerfile
    ports: ["5000:8080"]
    environment:
      - ASPNETCORE_ENVIRONMENT=Development
      - Security__PartnerSecrets__partner-01=docker-secret-partner-01
      - ExternalApi__BaseUrl=http://partner-external-api:5241
      - RabbitMQ__Host=rabbitmq
    depends_on: [rabbitmq, partner-external-api]
```