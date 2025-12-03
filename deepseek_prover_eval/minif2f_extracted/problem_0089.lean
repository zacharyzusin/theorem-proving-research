import Mathlib

open Real Nat Topology
open scoped BigOperators

theorem induction_prod1p1onk3le3m1onn
  (n : ℕ)
  (h₀ : 0 < n) :
  ∏ k in Finset.Icc 1 n, (1 + 1 / k^3) ≤ 3 - 1 / ↑n := sorry

