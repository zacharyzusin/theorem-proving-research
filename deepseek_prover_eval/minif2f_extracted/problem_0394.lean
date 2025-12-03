import Mathlib

open Real Nat Topology
open scoped BigOperators

theorem mathd_algebra_493
  (f : ℝ → ℝ)
  (h₀ : ∀ x, f x = x^2 - 4 * Real.sqrt x + 1) :
  f (f 4) = 70 := sorry
