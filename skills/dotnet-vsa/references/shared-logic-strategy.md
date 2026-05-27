# Shared Logic Strategy — 3-Tier Model & Anti-Patterns

## Three-Tier Sharing Model

| Tier | What | Share? | Location | Example |
|------|------|--------|----------|---------|
| **1: Technical Infrastructure** | `DbContext`, logging, auth, middleware, processors, groups | ✅ Freely | `Shared/`, `Infrastructure/` | `AppDbContext`, `GlobalExceptionHandlerMiddleware`, `RequestLoggingProcessor` |
| **2: Domain Concepts** | Entities, value objects with business rules, domain events | ✅ With care | `Shared/Domain/` or separate domain project | `Money` value object, `Order` entity with status transitions |
| **3: Feature-Specific Logic** | Validation, request/response DTOs per use case | ❌ Never | `Features/{Domain}/{Action}/` | `CreateOrderValidator`, `CreateOrderRequest` |

## Rule of Three

Don't extract shared code until you see the **same logic in 3+ places**:
1. **1 copy** — just write it, no abstraction needed
2. **2 copies** — tolerable, they may diverge
3. **3 copies** — extract to Tier 1 (infrastructure) or Tier 2 (domain concept)

**Why:** Two identical-looking snippets may evolve differently. Premature abstraction = coupling between features that should change independently.

## Shared Behaviors — Processors, Not Models

When multiple endpoints need the same cross-cutting behavior:

| Dimension | Share? | Mechanism |
|-----------|--------|-----------|
| **Cross-cutting logic** (logging, timing) | ✅ Share | Global pre/post-processors |
| **Group-level behavior** (auth, tenant) | ✅ Share | Route groups with processors |
| **Request/response DTOs** | ❌ Separate | One per endpoint |
| **Validators** | ❌ Separate | One per request type |
| **Domain entities** | ✅ Share | Tier 2 `Shared/Domain/` |
| **Business logic** | ✅ Share | Domain entity methods (not in handler) |

**Key insight:** Behaviors and models are orthogonal. Two endpoints can share a processor while having completely separate request/response types.

```csharp
// ✅ Correct: shared behavior, separate models
public class OrderGroup : Group {
    public OrderGroup() {
        Configure("orders", ep => {
            ep.PreProcessor<RequestLoggingProcessor>();  // shared behavior
        });
    }
}

public class CreateOrderEndpoint : Endpoint<CreateOrderRequest, Result<OrderDto>> {
    // separate model
}

public class CancelOrderEndpoint : Endpoint<CancelOrderRequest, Result<OrderDto>> {
    // separate model, same group = shared behavior
}

// ❌ Wrong: shared model across endpoints
public class OrderRequest { ... } // used by both Create and Cancel
```

## Push Logic Down — Avoid Anemic Domain Model

### ❌ Anemic — Logic in Handler

```csharp
public override async Task HandleAsync(CreateOrderRequest req, CancellationToken ct) {
    if (req.Items.Count == 0) {
        AddError(r => r.Items, "Order must have items");
        ThrowIfAnyErrors();
    }
    var total = req.Items.Sum(i => i.Price * i.Quantity);
    if (total <= 0) {
        AddError(r => r.Items, "Total must be positive");
        ThrowIfAnyErrors();
    }
    var order = new Order {
        CustomerId = req.CustomerId,
        Items = req.Items.Select(i => new OrderItem { ... }).ToList(),
        Total = total,
        Status = OrderStatus.Created,
        CreatedAt = DateTime.UtcNow
    };
    Db.Orders.Add(order);
    await Db.SaveChangesAsync(ct);
    await Send.CreatedAsync($"/api/v1/orders/{order.Id}",
        Result<OrderDto>.Ok(new OrderDto(order.Id, "Created")));
}
```

Problem: business rules scattered in handlers, duplicated across slices.

### ✅ Rich — Logic in Domain Object

```csharp
// Features/Orders/Create/CreateOrderEndpoint.cs
public override async Task HandleAsync(CreateOrderRequest req, CancellationToken ct) {
    var order = Order.Create(req.CustomerId, req.Items); // domain logic encapsulated
    Db.Orders.Add(order);
    await Db.SaveChangesAsync(ct);
    await Send.CreatedAsync($"/api/v1/orders/{order.Id}",
        Result<OrderDto>.Ok(new OrderDto(order.Id, "Created")));
}

// Shared/Domain/Order.cs
public class Order {
    public Guid Id { get; private set; }
    public Guid CustomerId { get; private set; }
    public OrderStatus Status { get; private set; }
    public decimal Total { get; private set; }
    public IReadOnlyList<OrderItem> Items => _items.AsReadOnly();
    private readonly List<OrderItem> _items = [];

    public static Order Create(Guid customerId, List<OrderItemDto> items) {
        if (items.Count == 0)
            throw new DomainException("Order must have items");
        var order = new Order {
            Id = Guid.NewGuid(),
            CustomerId = customerId,
            Status = OrderStatus.Created,
            CreatedAt = DateTime.UtcNow
        };
        foreach (var item in items)
            order.AddItem(item.ProductId, item.Quantity, item.Price);
        order.RecalculateTotal();
        return order;
    }

    public void AddItem(Guid productId, int quantity, decimal price) {
        if (quantity <= 0) throw new DomainException("Quantity must be positive");
        _items.Add(new OrderItem(productId, quantity, price));
    }

    private void RecalculateTotal() {
        Total = _items.Sum(i => i.LineTotal);
    }
}
```

Benefit: business rules centralized, testable without HTTP context, reusable across slices.

## Junk Drawer Anti-Pattern

### ❌ Shared Becomes Junk Drawer

```
Shared/
├── Helpers/              ← vague name = junk drawer
│   ├── StringHelper.cs   ← what does this even do?
│   ├── DateHelper.cs     ← date parsing? formatting? validation?
│   └── MathHelper.cs    ← why?
├── Services/             ← god services
│   └── OrderCalculationService.cs  ← handles cart totals, revenue, invoices
├── Extensions/           ← catch-all
│   └── EverythingExtensions.cs
└── Constants/             ← magic values without context
    └── AppConstants.cs   ← 500 lines of unrelated constants
```

### ✅ Organized Shared (Tier 1 Only)

```
Shared/
├── Domain/               ← Tier 2: Rich domain objects
│   ├── Order.cs
│   ├── Money.cs
│   └── OrderStatus.cs
├── Contracts/             ← Tier 1: Response records, external API interfaces
│   ├── IPartnerClient.cs
│   └── Responses.cs
├── Groups/                ← Tier 1: Route group definitions
│   ├── OrderGroup.cs
│   └── PartnerGroup.cs
├── Processors/            ← Tier 1: Cross-cutting processors
│   ├── RequestLoggingProcessor.cs
│   └── ResponseTimingProcessor.cs
└── Middleware/            ← Tier 1: ASP.NET middleware
    └── GlobalExceptionHandlerMiddleware.cs
```

## Checklist: Is This Shared Code or Junk?

Before adding code to `Shared/`, ask:
- [ ] **Is this infrastructure?** (DbContext, auth, logging, processors) → Tier 1, share freely
- [ ] **Is this a domain concept with behavior?** (entity, value object) → Tier 2, share carefully
- [ ] **Is this feature-specific?** (validation, request DTO, response DTO) → Tier 3, keep in feature slice
- [ ] **Can I name it precisely?** If not, it's likely junk → don't share
- [ ] **Have I seen this in 3+ places?** If not, duplicate for now → Rule of Three

## When to Split into a Separate Domain Project

If your domain layer (Tier 2) grows beyond ~20 files:

```
src/
├── MyApp.Api/             ← endpoints, DI, groups, processors
├── MyApp.Domain/          ← entities, value objects, domain events
│   ├── Orders/
│   │   ├── Order.cs
│   │   ├── OrderStatus.cs
│   │   └── Money.cs
│   └── Shared/            ← domain-wide value objects only
│       └── Email.cs
└── MyApp.Tests/
```

Only split when domain complexity justifies it — not prematurely.
