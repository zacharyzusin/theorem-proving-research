import Mathlib

open Real Nat Topology
open scoped BigOperators

theorem mathd_algebra_433
  (f : ℝ → ℝ)
  (h₀ : ∀ x, f x = 3 * Real.sqrt (2 * x - 7) - 8) :
  f 8 = 1 := sorry
