import Mathlib

open Real Nat Topology
open scoped BigOperators

theorem amc12_2001_p9
  (f : ℝ → ℝ)
  (h₀ : ∀ x > 0, ∀ y > 0, f (x * y) = f x / y)
  (h₁ : f 500 = 3) : f 600 = 5 / 2 := sorry
