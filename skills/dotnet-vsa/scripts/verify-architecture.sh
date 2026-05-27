#!/usr/bin/env bash
# verify-architecture.sh — Check .NET VSA project architecture compliance (FastEndpoints)
# Usage: ./verify-architecture.sh [project-path]
# Exit codes: 0=all checks pass, 1=violations found

PROJECT_DIR="${1:-.}"
VIOLATIONS=0
WARNINGS=0

RED='\033[0;31m'
YELLOW='\033[0;33m'
GREEN='\033[0;32m'
NC='\033[0m'

pass() { echo -e "${GREEN}  ✓${NC} $1"; }
fail() { echo -e "${RED}  ✗${NC} $1"; ((VIOLATIONS++)); }
warn() { echo -e "${YELLOW}  ⚠${NC} $1"; ((WARNINGS++)); }
header() { echo -e "\n$1"; }

CSPROJ=$(find "$PROJECT_DIR" -name "*.csproj" -not -path "*/bin/*" -not -path "*/obj/*" -not -path "*/Test*/*" 2>/dev/null | head -1)

header "=== .NET VSA Architecture Verification (FastEndpoints) ==="

# ─── 1. Project Structure ───
header "1. Project Structure"

[ -d "$PROJECT_DIR/Features" ] && pass "Features/ directory exists" || fail "Missing Features/ directory"
[ -d "$PROJECT_DIR/Infrastructure" ] && pass "Infrastructure/ directory exists" || fail "Missing Infrastructure/ directory"
[ -d "$PROJECT_DIR/Shared" ] && pass "Shared/ directory exists" || fail "Missing Shared/ directory"

FEATURE_DIRS=$(find "$PROJECT_DIR/Features" -mindepth 2 -maxdepth 2 -type d 2>/dev/null | wc -l)
[ "$FEATURE_DIRS" -gt 0 ] && pass "Feature slices found ($FEATURE_DIRS)" || warn "No feature slice folders found under Features/"

# Check for FastEndpoints-named folders
[ -d "$PROJECT_DIR/Shared/Groups" ] && pass "Shared/Groups/ directory exists (route groups)" || warn "Missing Shared/Groups/ — create for route group definitions"
[ -d "$PROJECT_DIR/Shared/Processors" ] && pass "Shared/Processors/ directory exists (pre/post-processors)" || warn "Missing Shared/Processors/ — create for cross-cutting processors"

# ─── 2. FastEndpoints Convention ───
header "2. FastEndpoints Convention"

ENDPOINT_FILES=$(grep -rl "Endpoint<" "$PROJECT_DIR/Features" --include="*.cs" 2>/dev/null || true)
if [ -n "$ENDPOINT_FILES" ]; then
    ENDPOINT_COUNT=$(echo "$ENDPOINT_FILES" | wc -l)
    pass "FastEndpoints endpoint classes found ($ENDPOINT_COUNT)"
else
    fail "No FastEndpoints endpoint classes found (expected Endpoint<TRequest, TResponse>)"
fi

# Check for legacy IEndpoint pattern
LEGACY_IENDPOINT=$(grep -rl "IEndpoint" "$PROJECT_DIR/Features" --include="*.cs" 2>/dev/null || true)
if [ -n "$LEGACY_IENDPOINT" ]; then
    fail "Legacy IEndpoint pattern found — migrate to FastEndpoints Endpoint<TReq, TRes>"
else
    pass "No legacy IEndpoint pattern detected"
fi

# Check Configure method
CONFIGURE_METHODS=$(grep -rn "override void Configure" "$PROJECT_DIR/Features" --include="*.cs" 2>/dev/null || true)
[ -n "$CONFIGURE_METHODS" ] && pass "Configure() overrides found" || warn "No Configure() overrides found in Features/"

# Check HandleAsync method
HANDLEASYNC_METHODS=$(grep -rn "override async Task HandleAsync" "$PROJECT_DIR/Features" --include="*.cs" 2>/dev/null || true)
[ -n "$HANDLEASYNC_METHODS" ] && pass "HandleAsync() overrides found" || warn "No HandleAsync() overrides found in Features/"

# Check authorization (Policies or AllowAnonymous)
POLICIES=$(grep -rn "Policies(" "$PROJECT_DIR/Features" --include="*.cs" 2>/dev/null || true)
ALLOW_ANON=$(grep -rn "AllowAnonymous()" "$PROJECT_DIR/Features" --include="*.cs" 2>/dev/null || true)
if [ -n "$POLICIES" ] || [ -n "$ALLOW_ANON" ]; then
    pass "Authorization configured on endpoints (Policies or AllowAnonymous)"
else
    warn "No Policies() or AllowAnonymous() on endpoints — verify if intentional"
fi

# ─── 3. FluentValidation ───
header "3. FluentValidation"

VALIDATORS=$(grep -rl "Validator<\|AbstractValidator" "$PROJECT_DIR" --include="*.cs" 2>/dev/null || true)
if [ -n "$VALIDATORS" ]; then
    VALIDATOR_COUNT=$(echo "$VALIDATORS" | wc -l)
    pass "FluentValidation validators found ($VALIDATOR_COUNT)"
else
    warn "No FluentValidation validators found"
fi

if [ -f "$PROJECT_DIR/Program.cs" ]; then
    grep -q "AddValidatorsFromAssembly" "$PROJECT_DIR/Program.cs" 2>/dev/null && pass "Validators auto-registered via AddValidatorsFromAssembly" || fail "AddValidatorsFromAssembly not found in Program.cs"
fi

# ─── 4. Authentication ───
header "4. Authentication"

AUTH_HANDLER=$(find "$PROJECT_DIR" -name "*AuthenticationHandler*.cs" -not -path "*/bin/*" -not -path "*/obj/*" 2>/dev/null | head -1)
if [ -n "$AUTH_HANDLER" ]; then
    pass "Authentication handler found"
    grep -q "FixedTimeEquals" "$AUTH_HANDLER" 2>/dev/null && pass "FixedTimeEquals used for timing-safe comparison" || fail "FixedTimeEquals NOT used — vulnerable to timing attacks"
    TIMESTAMP_LINES=$(grep -n "Timestamp\|timestamp" "$AUTH_HANDLER" 2>/dev/null || true)
    if echo "$TIMESTAMP_LINES" | grep -qi "expire\|skew\|tolerance\|valid\|window\|maxage" 2>/dev/null; then
        pass "Timestamp expiration/validation found"
    else
        warn "No timestamp expiration check — vulnerable to replay attacks"
    fi
else
    warn "No authentication handler found"
fi

# ─── 5. Resilience ───
header "5. Resilience Pipeline"

if [ -f "$PROJECT_DIR/Program.cs" ]; then
    if grep -q "AddStandardResilienceHandler" "$PROJECT_DIR/Program.cs" 2>/dev/null; then
        pass "Using AddStandardResilienceHandler (production-ready)"
    elif grep -q "AddResilienceHandler" "$PROJECT_DIR/Program.cs" 2>/dev/null; then
        warn "Using custom AddResilienceHandler — verify circuit breaker and jitter are included"
        grep -q "CircuitBreaker\|circuit" "$PROJECT_DIR/Program.cs" 2>/dev/null && pass "Circuit breaker configured" || fail "No circuit breaker in resilience pipeline"
        grep -q "UseJitter" "$PROJECT_DIR/Program.cs" 2>/dev/null && pass "Jitter enabled on retry" || warn "No jitter on retry — thundering herd risk"
        grep -q "TotalRequestTimeout\|AddTimeout" "$PROJECT_DIR/Program.cs" 2>/dev/null && pass "Timeout configured" || warn "No total request timeout configured"
    elif grep -q "AddRefitClient\|HttpClient" "$PROJECT_DIR/Program.cs" 2>/dev/null; then
        warn "HTTP client without resilience pipeline"
    else
        pass "No HTTP client (nothing to check)"
    fi
fi

# ─── 6. Message Queue ───
header "6. Message Queue (RabbitMQ)"

MQ_IMPL=$(find "$PROJECT_DIR" \( -name "*MessageQueue*" -o -name "*RabbitMq*" \) -name "*.cs" -not -path "*/bin/*" -not -path "*/obj/*" 2>/dev/null | grep -v "Interface\|IMessage" || true)
if [ -n "$MQ_IMPL" ]; then
    pass "Message queue implementation found"
    MQ_IMPL_FILES=$(echo "$MQ_IMPL" | grep -v "^.*IMessageQueueService.cs$" || true)
    for f in $MQ_IMPL_FILES; do
        grep -q "AutomaticRecoveryEnabled" "$f" 2>/dev/null && pass "RabbitMQ auto-recovery enabled" || fail "RabbitMQ AutomaticRecoveryEnabled NOT set — connection drops cause manual restart"
        grep -q "TopologyRecoveryEnabled" "$f" 2>/dev/null && pass "RabbitMQ topology recovery enabled" || warn "RabbitMQ TopologyRecoveryEnabled NOT set"
        grep -q "_connection!" "$f" 2>/dev/null && warn "Potential null reference on _connection! — add null-check or wait logic" || true
    done
else
    pass "No message queue (nothing to check)"
fi

# ─── 7. FastEndpoints Registration ───
header "7. FastEndpoints Registration"

if [ -f "$PROJECT_DIR/Program.cs" ]; then
    grep -q "AddFastEndpoints" "$PROJECT_DIR/Program.cs" 2>/dev/null && pass "AddFastEndpoints() found in Program.cs" || fail "AddFastEndpoints() not found — required for FastEndpoints"
    grep -q "UseFastEndpoints" "$PROJECT_DIR/Program.cs" 2>/dev/null && pass "UseFastEndpoints() found in Program.cs" || fail "UseFastEndpoints() not found — required for FastEndpoints pipeline"
fi

# Check for route groups
GROUP_FILES=$(find "$PROJECT_DIR" -name "*Group*.cs" -not -path "*/bin/*" -not -path "*/obj/*" 2>/dev/null)
if [ -n "$GROUP_FILES" ]; then
    GROUP_COUNT=$(echo "$GROUP_FILES" | wc -l)
    pass "Route group definitions found ($GROUP_COUNT)"
else
    warn "No route group definitions found — consider using Groups for shared behaviors"
fi

# Check for processors
PROCESSOR_FILES=$(find "$PROJECT_DIR" -name "*Processor*.cs" -not -path "*/bin/*" -not -path "*/obj/*" 2>/dev/null)
if [ -n "$PROCESSOR_FILES" ]; then
    PROCESSOR_COUNT=$(echo "$PROCESSOR_FILES" | wc -l)
    pass "Pre/Post-processor definitions found ($PROCESSOR_COUNT)"
else
    warn "No pre/post-processors found — consider adding for logging, timing, etc."
fi

# ─── 8. Code Style ───
header "8. Code Style"

CS_FILES=$(find "$PROJECT_DIR" -name "*.cs" -not -path "*/bin/*" -not -path "*/obj/*" 2>/dev/null)
TOTAL_CS=$(echo "$CS_FILES" | wc -l)
FILE_NS=$(grep -rl "^namespace " "$PROJECT_DIR" --include="*.cs" 2>/dev/null | while read f; do head -5 "$f" | grep -c "^namespace .*;\$" 2>/dev/null; done | grep -c "1" || true)
BLOCK_NS=$(grep -rl "^namespace .*{" "$PROJECT_DIR" --include="*.cs" 2>/dev/null | wc -l)

if [ "$FILE_NS" -gt "$BLOCK_NS" ] 2>/dev/null; then
    pass "Using file-scoped namespaces (preferred)"
else
    warn "Using block-scoped namespaces — prefer file-scoped (C# 10+)"
fi

# .editorconfig
if [ -f "$PROJECT_DIR/.editorconfig" ] || [ -f "$(dirname "$PROJECT_DIR")/.editorconfig" ]; then
    pass ".editorconfig found"
else
    warn "No .editorconfig found — run: dotnet-vsa generate-editorconfig"
fi

# ─── 9. Testing ───
header "9. Testing"

PARENT_DIR=$(dirname "$PROJECT_DIR")
TEST_DIR=$(find "$PARENT_DIR" -maxdepth 1 -name "*Tests*" -type d 2>/dev/null | head -1)
if [ -n "$TEST_DIR" ] && [ -d "$TEST_DIR" ]; then
    pass "Test project found"
    TEST_CS=$(find "$TEST_DIR" -name "*.cs" -not -path "*/bin/*" -not -path "*/obj/*" 2>/dev/null | wc -l)
    SRC_CS=$(find "$PROJECT_DIR" -name "*.cs" -not -path "*/bin/*" -not -path "*/obj/*" 2>/dev/null | wc -l)
    if [ "$SRC_CS" -gt 0 ]; then
        echo "  ℹ  Test/Source ratio: $TEST_CS/$SRC_CS"
    fi
    # Check test folder mirrors source structure
    FEATURE_DOMAINS=$(find "$PROJECT_DIR/Features" -mindepth 1 -maxdepth 1 -type d 2>/dev/null | while read d; do basename "$d"; done | sort)
    TEST_FEATURE_DOMAINS=$(find "$TEST_DIR/Features" -mindepth 1 -maxdepth 1 -type d 2>/dev/null | while read d; do basename "$d"; done | sort)
    if [ -n "$FEATURE_DOMAINS" ] && [ -n "$TEST_FEATURE_DOMAINS" ]; then
        MISMATCH=$(comm -23 <(echo "$FEATURE_DOMAINS") <(echo "$TEST_FEATURE_DOMAINS") 2>/dev/null)
        if [ -z "$MISMATCH" ]; then
            pass "Test folder structure mirrors Features/ structure"
        else
            warn "Test folder missing coverage for: $(echo $MISMATCH | tr '\n' ', ')"
        fi
    else
        warn "No Features/ folder found in test project — mirror source structure"
    fi
    # Check architecture tests
    ARCH_TESTS=$(find "$TEST_DIR" -name "*Architecture*" -name "*.cs" -not -path "*/bin/*" 2>/dev/null)
    if [ -n "$ARCH_TESTS" ]; then
        pass "Architecture tests found"
    else
        warn "No architecture tests found — add tests enforcing FastEndpoints conventions"
    fi
else
    warn "No test project found"
fi

# ─── 10. Domain Model Quality ───
header "10. Domain Model Quality"

CS_ENTITY_FILES=$(find "$PROJECT_DIR/Shared/Domain" -name "*.cs" -not -path "*/bin/*" 2>/dev/null)
if [ -n "$CS_ENTITY_FILES" ]; then
    ANEMIC_COUNT=0
    for f in $CS_ENTITY_FILES; do
        HAS_METHODS=$(grep -c "public.*void\|public.*Task\|public static\|private.*void\|private static" "$f" 2>/dev/null || echo "0")
        HAS_ONLY_PROPS=$(grep -c "{ get; set; }" "$f" 2>/dev/null || echo "0")
        if [ "$HAS_METHODS" -eq 0 ] && [ "$HAS_ONLY_PROPS" -gt 0 ]; then
            warn "Anemic domain model: $(basename "$f") has only { get; set; } properties and no behavior — push logic into domain objects"
            ((ANEMIC_COUNT++))
        fi
    done
    if [ "$ANEMIC_COUNT" -eq 0 ]; then
        pass "Domain objects have behavior (no anemic models detected)"
    fi
else
    pass "No Shared/Domain/ folder (no domain objects to check)"
fi

# ─── 11. Shared Logic Hygiene ───
header "11. Shared Logic Hygiene"

SHARED_DIR="$PROJECT_DIR/Shared"
if [ -d "$SHARED_DIR" ]; then
    # Check for vague folder names that indicate junk drawer
    JUNK_FOLDERS=$(find "$SHARED_DIR" -maxdepth 1 -type d \( -name "Helpers" -o -name "Utils" -o -name "Common" -o -name "Misc" \) 2>/dev/null)
    if [ -n "$JUNK_FOLDERS" ]; then
        for f in $JUNK_FOLDERS; do
            warn "Potential junk drawer: $(basename "$f")/ — consider moving contents to specific feature slices or Tier 1/2 locations"
        done
    else
        pass "No junk drawer folders detected in Shared/"
    fi

    # Check for business logic in Shared (should be in feature slices)
    SHARED_CS=$(find "$SHARED_DIR" -name "*.cs" -not -path "*/bin/*" -not -path "*/obj/*" 2>/dev/null)
    SHARED_HANDLER_COUNT=0
    for f in $SHARED_CS; do
        grep -q "HandleAsync\|IResult\|Task<IResult>" "$f" 2>/dev/null && ((SHARED_HANDLER_COUNT++))
    done
    if [ "$SHARED_HANDLER_COUNT" -gt 0 ]; then
        fail "Found $SHARED_HANDLER_COUNT handler(s) in Shared/ — endpoint logic belongs in Features/ slices"
    else
        pass "No endpoint handler logic in Shared/"
    fi
else
    pass "No Shared/ folder (nothing to check)"
fi

# ─── 12. Response Type Safety ───
header "12. Response Type Safety"

# Check for Send method usage (FastEndpoints pattern)
SEND_METHODS=$(grep -rn "SendAsync\|Send\.Ok\|Send\.Created\|Send\.Accepted\|Send\.NotFound" "$PROJECT_DIR/Features" --include="*.cs" 2>/dev/null | wc -l)
if [ "$SEND_METHODS" -gt 0 ]; then
    pass "FastEndpoints Send methods used ($SEND_METHODS occurrences)"
else
    warn "No FastEndpoints Send methods detected — verify response pattern"
fi

# Check for typed response records
RESPONSE_RECORDS=$(grep -rn "record.*Response" "$PROJECT_DIR" --include="*.cs" 2>/dev/null | wc -l)
if [ "$RESPONSE_RECORDS" -gt 0 ]; then
    pass "Typed response records found ($RESPONSE_RECORDS)"
else
    warn "No typed response records found — consider defining Result<T> and PagedData<T>"
fi

# ─── Summary ───
header "=== Summary ==="
echo -e "  Violations: ${RED}$VIOLATIONS${NC}"
echo -e "  Warnings:   ${YELLOW}$WARNINGS${NC}"

echo ""
echo "  Checks: 12 (Structure, FastEndpoints, Validation, Auth, Resilience, MQ, Registration, Code Style, Testing, Domain Model, Shared Hygiene, Response Types)"

if [ "$VIOLATIONS" -gt 0 ]; then
    echo -e "\n${RED}ARCHITECTURE CHECK FAILED${NC} — $VIOLATIONS violation(s) found"
    exit 1
else
    echo -e "\n${GREEN}ARCHITECTURE CHECK PASSED${NC} — $WARNINGS warning(s)"
    exit 0
fi