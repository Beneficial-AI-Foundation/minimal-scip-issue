//! Minimal example demonstrating SCIP symbol format differences.
//!
//! This crate shows four cases:
//! 1. Owned Self: `impl Neg for Scalar` - works correctly in both tools
//! 2. Reference Self: `impl Neg for &Scalar` - verus-analyzer omits the Self type
//! 3. Duplicate symbols (Mul): Two different `Mul` impls produce identical symbols
//! 4. Duplicate symbols (From): Generic type params lost, causing duplicates

use std::ops::{Mul, Neg};

/// A simple scalar type for demonstration.
#[derive(Clone, Copy, Debug)]
pub struct Scalar(pub i32);

/// A simple point type for demonstration.
#[derive(Clone, Copy, Debug)]
pub struct Point(pub i32, pub i32);

// =============================================================================
// Case 1: Owned Self - both tools handle this correctly
// =============================================================================

/// Expected symbols:
/// - rust-analyzer: `impl#[Scalar][Neg]neg().`
/// - verus-analyzer: `Scalar#Neg#neg().`
impl Neg for Scalar {
    type Output = Scalar;

    fn neg(self) -> Scalar {
        Scalar(-self.0)
    }
}

// =============================================================================
// Case 2: Reference Self - verus-analyzer omits the Self type
// =============================================================================

/// Expected symbols:
/// - rust-analyzer: `impl#[`&Scalar`][Neg]neg().`
/// - verus-analyzer: `Neg#neg().`  <-- Missing the `&Scalar` Self type!
impl Neg for &Scalar {
    type Output = Scalar;

    fn neg(self) -> Scalar {
        Scalar(-self.0)
    }
}

// =============================================================================
// Case 3: Duplicate symbols - two distinct impls produce identical symbols
// =============================================================================

/// Multiply a point reference by a scalar reference.
///
/// Expected symbols:
/// - rust-analyzer: `impl#[`&Point`][`Mul<&Scalar>`]mul().`
/// - verus-analyzer: `Mul#mul().`
impl Mul<&Scalar> for &Point {
    type Output = Point;

    fn mul(self, scalar: &Scalar) -> Point {
        Point(self.0 * scalar.0, self.1 * scalar.0)
    }
}

/// Multiply a scalar reference by a point reference.
///
/// Expected symbols:
/// - rust-analyzer: `impl#[`&Scalar`][`Mul<&Point>`]mul().`
/// - verus-analyzer: `Mul#mul().`  <-- DUPLICATE! Same as above!
impl Mul<&Point> for &Scalar {
    type Output = Point;

    fn mul(self, point: &Point) -> Point {
        Point(self.0 * point.0, self.0 * point.1)
    }
}

// =============================================================================
// Case 4: From trait with generic type parameters - duplicates due to lost generics
// =============================================================================

/// A generic container type, similar to LookupTable<T> in curve25519-dalek.
#[derive(Debug)]
pub struct Container<T> {
    pub value: T,
}

/// Marker type A (like ProjectiveNielsPoint in curve25519-dalek).
#[derive(Debug, Clone, Copy)]
pub struct TypeA;

/// Marker type B (like AffineNielsPoint in curve25519-dalek).
#[derive(Debug, Clone, Copy)]
pub struct TypeB;

/// Convert from Scalar to Container<TypeA>.
///
/// Expected symbols:
/// - rust-analyzer: `impl#[`Container<TypeA>`][`From<&Scalar>`]from().`
/// - verus-analyzer: `Container#From#from().`
impl From<&Scalar> for Container<TypeA> {
    fn from(_s: &Scalar) -> Self {
        Container { value: TypeA }
    }
}

/// Convert from Scalar to Container<TypeB>.
///
/// Expected symbols:
/// - rust-analyzer: `impl#[`Container<TypeB>`][`From<&Scalar>`]from().`
/// - verus-analyzer: `Container#From#from().`  <-- DUPLICATE! Same as above!
impl From<&Scalar> for Container<TypeB> {
    fn from(_s: &Scalar) -> Self {
        Container { value: TypeB }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_neg_owned() {
        let s = Scalar(5);
        assert_eq!((-s).0, -5);
    }

    #[test]
    fn test_neg_ref() {
        let s = Scalar(5);
        assert_eq!((-&s).0, -5);
    }

    #[test]
    fn test_mul_point_by_scalar() {
        let p = Point(2, 3);
        let s = Scalar(4);
        let result = &p * &s;
        assert_eq!(result.0, 8);
        assert_eq!(result.1, 12);
    }

    #[test]
    fn test_mul_scalar_by_point() {
        let s = Scalar(4);
        let p = Point(2, 3);
        let result = &s * &p;
        assert_eq!(result.0, 8);
        assert_eq!(result.1, 12);
    }

    #[test]
    fn test_from_scalar_to_container_a() {
        let s = Scalar(5);
        let _c: Container<TypeA> = Container::from(&s);
        // Just verify it compiles and runs
    }

    #[test]
    fn test_from_scalar_to_container_b() {
        let s = Scalar(5);
        let _c: Container<TypeB> = Container::from(&s);
        // Just verify it compiles and runs
    }
}

