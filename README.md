# Minimal SCIP Symbol Issue Example

A minimal reproducible example demonstrating SCIP symbol format differences between rust-analyzer and verus-analyzer.

## The Issue

When generating SCIP indices, verus-analyzer seems to omit the Self type from symbols when Self is a reference.

## Test Cases in `src/lib.rs`

### Case 1: Owned Self 
```rust
impl Neg for Scalar { ... }
```
Both tools handle this correctly.

### Case 2: Reference Self 
```rust
impl Neg for &Scalar { ... }
```
- **rust-analyzer**: `` `impl#[`&Scalar`][Neg]neg().` ``
- **verus-analyzer**: `Neg#neg().` (missing `&Scalar`!)

### Case 3: Duplicate Symbols (Mul)
```rust
impl Mul<&Scalar> for &Point { ... }
impl Mul<&Point> for &Scalar { ... }
```
Both produce `Mul#mul().` in verus-analyzer.

### Case 4: Duplicate Symbols (From with generics)
```rust
impl From<&Scalar> for Container<TypeA> { ... }
impl From<&Scalar> for Container<TypeB> { ... }
```
- **rust-analyzer**: 
  - `` impl#[`Container<TypeA>`][`From<&Scalar>`]from(). ``
  - `` impl#[`Container<TypeB>`][`From<&Scalar>`]from(). ``
- **verus-analyzer**: Both produce `Container#From#from().` (duplicate!)

## Generating SCIP Output

### rust-analyzer

```bash
# Generate SCIP index
rust-analyzer scip . 

# Convert to JSON for inspection
scip print index.scip > index-ra.json
# Or use: cargo run --release -- scip-to-json index-ra.scip index-ra.json
```

### verus-analyzer

```bash
# Assuming verus-analyzer is installed and in PATH
verus-analyzer scip . 

# Convert to JSON
scip print index.scip > index-va.json
```

## Expected Results

After generating both SCIP indices, use the Python script to extract impl symbols:

```bash
python3 extract_impl_symbols.py index-ra.json index-va.json
```

### rust-analyzer 

From `index-ra.json`:
```
impl#[Scalar][Neg]neg().
impl#[`&Scalar`][Neg]neg().
impl#[`&Point`][`Mul<&Scalar>`]mul().
impl#[`&Scalar`][`Mul<&Point>`]mul().
impl#[`Container<TypeA>`][`From<&Scalar>`]from().
impl#[`Container<TypeB>`][`From<&Scalar>`]from().

Unique symbols: 6
```

All six implementations have unique symbols.

### verus-analyzer 

From `index-va.json`:
```
Scalar#Neg#neg().
Neg#neg().
Mul#mul().           <-- duplicate (2 impls)
Container#From#from().  <-- duplicate (2 impls)

Unique symbols: 4 (but 6 implementations!)
```

Two `Mul` impls collapse into one symbol, and two `From` impls collapse into one symbol.

## Note on Type Information Recovery

The type information missing from `verus-analyzer` symbols *is* present elsewhere in the SCIP index. For example, signature documentation includes turbofish-style type parameters:

```
// From index-va.json, the signature shows the concrete type:
"text": "fn from(_s: &Scalar) -> Container<TypeA>"
```

However, this information is not encoded in the symbol itself (`Container#From#from().`), which means:
- symbol-based lookups will incorrectly merge distinct implementations
- recovering unique identifiers would require ad-hoc reconstruction by parsing signatures or other metadata.

In contrast, `rust-analyzer` encodes the type information directly in the symbol (`impl#[\`Container<TypeA>\`][\`From<&Scalar>\`]from().`), making each implementation uniquely addressable without additional processing.

