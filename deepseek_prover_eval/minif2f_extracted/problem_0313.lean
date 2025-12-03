import Mathlib

open Real Nat Topology
open scoped BigOperators

theorem mathd_algebra_35
  (p q : ℝ → ℝ)
  (h₀ : ∀ x, p x = 2 - x^2)
  (h₁ : ∀ x, x ≠ 0 -> q x = 6 / x) :
  p (q 2) = -7 := sorry
