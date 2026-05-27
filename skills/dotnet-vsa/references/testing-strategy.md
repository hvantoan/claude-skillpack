# Testing Strategy for Vertical Slice Architecture

## Testing Pyramid

```
        ┌────────────┐
        │    E2E      │  ← Few, slow, full stack
        │   Tests     │     WebApplicationFactory + Testcontainers
        ├────────────┤
        │ Integration │  ← Medium, real DB + HTTP
        │   Tests     │     WebApplicationFactory + SQLite/PostgreSQL
        ├────────────┤
        │    Unit     │  ← Many, fast, isolated
        │   Tests     │     Test handler directly, mock only external deps
        └────────────┘
```

## Handler is the Test Boundary

In VSA, the **feature handler** is the primary test boundary. No need to test each layer separately.

```csharp
// ✅ Good: test handler directly — no HTTP host needed
public class CreateTransactionEndpointTests {
    [Fact]
    public async Task Handle_ValidRequest_ReturnsAccepted() {
        // Arrange
        var validator = new CreateTransactionValidator();
        var mockClient = new Mock<IPartnerClient>();
        mockClient.Setup(c => c.VerifyPartnerAsync("partner-01")).ReturnsAsync(true);
        var mockQueue = new Mock<IMessageQueueService>();

        // Act
        var result = await CreateTransactionEndpoint.Handle(
            request, validator, mockClient.Object, mockQueue.Object);

        // Assert
        var accepted = Assert.IsType<AcceptedHttpResult>(result);
        // ...
    }
}
```

## Unit Testing Handlers

### What to Test
- Handler logic (validation → external call → queue/persist → return)
- Domain object behavior (entity methods, value objects)
- Validator rules

### What NOT to Test Separately
- DI registration (test via integration tests)
- Middleware (test via integration tests)
- Framework behavior (model binding, routing)

### Mocking Strategy
- **Mock external dependencies**: `IPartnerClient`, `IMessageQueueService`
- **Use real validators**: FluentValidation validators are fast, no need to mock
- **Use `FakeTimeProvider`** instead of mocking `DateTime`

```csharp
// ✅ Use FakeTimeProvider
var timeProvider = new FakeTimeProvider();
timeProvider.SetUtcNow(new DateTime(2025, 1, 1, 12, 0, 0, DateTimeKind.Utc));

// ❌ Don't mock DateTime.UtcNow
var mockClock = new Mock<ISystemClock>();
```

## Integration Testing

### WebApplicationFactory Setup
```csharp
public class IntegrationTestFactory : WebApplicationFactory<Program> {
    protected override void ConfigureWebHost(IWebHostBuilder builder) {
        builder.ConfigureServices(services => {
            // Remove real DB, add SQLite in-memory
            var descriptor = services.SingleOrDefault(
                d => d.ServiceType == typeof(DbContextOptions<AppDbContext>));
            if (descriptor != null) services.Remove(descriptor);
            services.AddDbContext<AppDbContext>(options =>
                options.UseSqlite("DataSource=:memory:"));
        });
    }
}
```

### EF Core Provider Selection

| Provider | Use For | Speed | Fidelity |
|----------|--------|-------|----------|
| **InMemory** | Quick logic checks | Fast | Low (no relational constraints) |
| **SQLite in-memory** | Query/constraint testing | Fast | Medium (relational but limited) |
| **Testcontainers (PostgreSQL)** | Production-equivalent | Slow | High (same DB engine) |

### Test Pattern
```csharp
public class CreateTransactionIntegrationTests : IClassFixture<IntegrationTestFactory> {
    private readonly HttpClient _client;

    public CreateTransactionIntegrationTests(IntegrationTestFactory factory) {
        _client = factory.CreateClient();
    }

    [Fact]
    public async Task CreateTransaction_ValidRequest_ReturnsAccepted() {
        var response = await _client.PostAsJsonAsync("/api/v1/partner/transactions", new {
            PartnerId = "partner-01",
            Amount = 100,
            Currency = "USD"
        });
        response.StatusCode.Should().Be(HttpStatusCode.Accepted);
    }
}
```

## Architecture Tests

Enforce VSA conventions at compile time:

```csharp
[Fact]
public void Endpoints_ShouldImplementIEndpoint() {
    var endpointTypes = typeof(Program).Assembly.GetTypes()
        .Where(t => t.Name.EndsWith("Endpoint") && !t.IsAbstract);
    foreach (var type in endpointTypes) {
        typeof(IEndpoint).IsAssignableFrom(type).Should().BeTrue(
            $"{type.Name} should implement IEndpoint");
    }
}

[Fact]
public void Handlers_ShouldBeStatic() {
    var handlerMethods = typeof(Program).Assembly.GetTypes()
        .SelectMany(t => t.GetMethods())
        .Where(m => m.Name == "Handle");
    foreach (var method in handlerMethods) {
        method.IsStatic.Should().BeTrue(
            $"{method.DeclaringType?.Name}.Handle should be static");
    }
}

[Fact]
public void FeatureFolders_ShouldMirrorTestFolders() {
    // Verify test folder structure mirrors Features/ structure
    var srcFeatures = Directory.GetDirectories("Features", "*", SearchOption.AllDirectories);
    var testFeatures = Directory.GetDirectories("../MyApp.Tests/Features", "*", SearchOption.AllDirectories);
    // Assert structure matches
}
```

## Test Folder Structure

Mirror source structure in test project:
```
MyApp.Tests/
├── Features/
│   └── Transactions/
│       └── Create/
│           ├── CreateTransactionEndpointTests.cs    ← unit
│           ├── CreateTransactionValidatorTests.cs    ← unit
│           └── CreateTransactionIntegrationTests.cs  ← integration
├── Infrastructure/
│   ├── Auth/
│   │   └── HmacAuthenticationHandlerTests.cs
│   └── Messaging/
│       └── RabbitMqMessageQueueServiceTests.cs
└── Architecture/
    └── ArchitectureTests.cs
```

## Test Naming Convention

```
{MethodName}_{Scenario}_{ExpectedBehavior}

Examples:
- Handle_ValidRequest_ReturnsAccepted
- Handle_InvalidCurrency_ReturnsBadRequest
- Handle_VerificationFailed_Returns502
- Validate_EmptyPartnerId_Fails
- Create_ValidRequest_SetsStatusCreated  (domain object test)
```

## Checklist: VSA Test Coverage

- [ ] Each endpoint handler has corresponding unit test
- [ ] Each validator has dedicated test file
- [ ] Domain objects (entities, value objects) have behavior tests
- [ ] Integration tests cover happy path + auth for each endpoint
- [ ] Architecture tests enforce `IEndpoint` implementation
- [ ] Architecture tests enforce `Handle` is static
- [ ] Test folder structure mirrors `Features/` structure
- [ ] No test of framework behavior (model binding, routing)