import Mathlib

open Real Nat Topology
open scoped BigOperators

theorem imo_1978_p5
  (n : ℕ)
  (a : ℕ → ℕ)
  (h₀ : Function.Injective a)
  (h₁ : a 0 = 0)
  (h₂ : 0 < n) :
  (∑ k in Finset.Icc 1 n, 1/k) ≤ ∑ k in Finset.Icc 1 n, (a k)/k^(2) := sorry
