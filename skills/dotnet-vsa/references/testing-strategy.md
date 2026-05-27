# Testing Strategy for FastEndpoints + Vertical Slice Architecture

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
        │   Tests     │     Factory.Create<T>(), mock DI properties
        └────────────┘
```

## Handler is the Test Boundary

In VSA, the **endpoint handler** is the primary test boundary. No need to test each layer separately.

```csharp
// ✅ Good: test endpoint handler via Factory.Create
public class CreateTransactionEndpointTests {
    [Fact]
    public async Task HandleAsync_ValidRequest_ReturnsAccepted() {
        // Arrange — create endpoint with mocked dependencies
        var mockClient = new Mock<IPartnerClient>();
        mockClient.Setup(c => c.VerifyPartnerAsync("partner-01")).ReturnsAsync(true);
        var mockQueue = new Mock<IMessageQueueService>();

        var ep = Factory.Create<CreateTransactionEndpoint>();
        ep.MapProperties(new {
            PartnerClient = mockClient.Object,
            MessageQueue = mockQueue.Object
        });

        var req = new CreateTransactionRequest {
            PartnerId = "partner-01",
            Amount = 100,
            Currency = "USD"
        };

        // Act
        await ep.HandleAsync(req, default);
        var response = ep.Response;

        // Assert
        Assert.False(ep.ValidationFailed);
        Assert.NotNull(response);
    }
}
```

## Unit Testing Endpoints

### Using Factory.Create

```csharp
// Simple endpoint with property injection
var ep = Factory.Create<CreateOrderEndpoint>();

// Set properties manually
ep.Db = mockDb.Object;
ep.Logger = mockLogger.Object;

// Execute
await ep.HandleAsync(req, default);

// Assert
Assert.NotNull(ep.Response);
```

### Using Constructor Injection

```csharp
// If endpoint uses constructor injection, pass mocks to Factory.Create
var ep = Factory.Create<CreateOrderEndpoint>(
    mockDb.Object,
    mockLogger.Object
);
```

### What to Test

- Endpoint handler logic (validation → external call → queue/persist → response)
- Domain object behavior (entity methods, value objects)
- Validator rules (FluentValidation — test directly)
- Pre/Post-processor logic

### What NOT to Test Separately

- DI registration (test via integration tests)
- Middleware (test via integration tests)
- FastEndpoints framework behavior (routing, model binding)
- Auto-validation (FluentValidation + FastEndpoints integration)

### Mocking Strategy

- **Mock external dependencies**: `IPartnerClient`, `IMessageQueueService`
- **Mock database**: `AppDbContext` or use in-memory provider
- **Use real validators**: FluentValidation validators are fast, no need to mock
- **Use `FakeTimeProvider`** instead of mocking `DateTime`

```csharp
// ✅ Use FakeTimeProvider
var timeProvider = new FakeTimeProvider();
timeProvider.SetUtcNow(new DateTime(2025, 1, 1, 12, 0, 0, DateTimeKind.Utc));

// ❌ Don't mock DateTime.UtcNow
var mockClock = new Mock<ISystemClock>();
```

## Unit Testing Validators

Validators are tested independently of endpoints:

```csharp
public class CreateTransactionValidatorTests {
    private readonly CreateTransactionValidator _validator = new();

    [Fact]
    public async Task Validate_ValidRequest_Passes() {
        var request = new CreateTransactionRequest {
            PartnerId = "partner-01",
            Amount = 100,
            Currency = "USD",
            Timestamp = DateTime.UtcNow
        };
        var result = await _validator.ValidateAsync(request);
        Assert.True(result.IsValid);
    }

    [Fact]
    public async Task Validate_InvalidCurrency_Fails() {
        var request = new CreateTransactionRequest {
            PartnerId = "partner-01",
            Amount = 100,
            Currency = "XYZ",
            Timestamp = DateTime.UtcNow
        };
        var result = await _validator.ValidateAsync(request);
        Assert.False(result.IsValid);
        Assert.Contains(result.Errors, e => e.PropertyName == "Currency");
    }
}
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

### Integration Test Pattern

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

Enforce VSA + FastEndpoints conventions at compile time:

```csharp
[Fact]
public void Endpoints_ShouldInheritFastEndpointsBase() {
    var endpointTypes = typeof(Program).Assembly.GetTypes()
        .Where(t => t.Name.EndsWith("Endpoint") && !t.IsAbstract);
    foreach (var type in endpointTypes) {
        // Should inherit from FastEndpoints.Endpoint<,>
        var baseType = type.BaseType;
        baseType.Should().NotBeNull($"{type.Name} should inherit from FastEndpoints.Endpoint");
        baseType!.IsGenericType.Should().BeTrue();
    }
}

[Fact]
public void Validators_ShouldInheritValidatorBase() {
    var validatorTypes = typeof(Program).Assembly.GetTypes()
        .Where(t => t.Name.EndsWith("Validator") && !t.IsAbstract);
    foreach (var type in validatorTypes) {
        // Should inherit from Validator<T> or AbstractValidator<T>
        var baseType = type.BaseType;
        baseType.Should().NotBeNull($"{type.Name} should inherit from Validator<T>");
    }
}

[Fact]
public void Groups_ShouldInheritGroupBase() {
    var groupTypes = typeof(Program).Assembly.GetTypes()
        .Where(t => t.Name.EndsWith("Group") && !t.IsAbstract && !t.IsInterface);
    foreach (var type in groupTypes) {
        typeof(FastEndpoints.Group).IsAssignableFrom(type).Should().BeTrue(
            $"{type.Name} should inherit from FastEndpoints.Group");
    }
}

[Fact]
public void FeatureFolders_ShouldMirrorTestFolders() {
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
├── Shared/
│   ├── Processors/
│   │   └── RequestLoggingProcessorTests.cs
│   └── Groups/
│       └── OrderGroupTests.cs
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
- HandleAsync_ValidRequest_ReturnsAccepted
- HandleAsync_InvalidCurrency_FailsValidation
- HandleAsync_VerificationFailed_Returns502
- Validate_EmptyPartnerId_Fails
- Create_ValidRequest_SetsStatusCreated  (domain object test)
- PreProcessAsync_MissingTenant_Returns400 (processor test)
```

## Checklist: VSA + FastEndpoints Test Coverage

- [ ] Each endpoint handler has corresponding unit test
- [ ] Each validator has dedicated test file
- [ ] Domain objects (entities, value objects) have behavior tests
- [ ] Pre/Post-processors have unit tests
- [ ] Integration tests cover happy path + auth for each endpoint
- [ ] Architecture tests enforce `Endpoint<TReq, TRes>` inheritance
- [ ] Architecture tests enforce `Validator<T>` inheritance
- [ ] Architecture tests enforce `Group` inheritance for route groups
- [ ] Test folder structure mirrors `Features/` structure
- [ ] No test of framework behavior (model binding, routing, auto-validation)
