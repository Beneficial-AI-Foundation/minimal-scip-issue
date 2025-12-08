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

### Case 3: Duplicate Symbols 
```rust
impl Mul<&Scalar> for &Point { ... }
impl Mul<&Point> for &Scalar { ... }
```
Both produce `Mul#mul().` in verus-analyzer.

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
L213: rust-analyzer cargo minimal-scip-issue 0.1.0 impl#[Scalar][Neg]neg().
L493: rust-analyzer cargo minimal-scip-issue 0.1.0 impl#[`&Point`][`Mul<&Scalar>`]mul().
L346: rust-analyzer cargo minimal-scip-issue 0.1.0 impl#[`&Scalar`][Neg]neg().
L746: rust-analyzer cargo minimal-scip-issue 0.1.0 impl#[`&Scalar`][`Mul<&Point>`]mul().

Unique symbols: 4
```

All four implementations have unique symbols.

### verus-analyzer 

From `index-va.json`:
```
L366: rust-analyzer cargo minimal-scip-issue 0.1.0 Mul#mul().  
L275: rust-analyzer cargo minimal-scip-issue 0.1.0 Neg#neg().
L192: rust-analyzer cargo minimal-scip-issue 0.1.0 Scalar#Neg#neg().

Unique symbols: 3
```


