import Mathlib

open Real Nat Topology
open scoped BigOperators

theorem amc12a_2016_p3
  (f : ℝ → ℝ → ℝ)
  (h₀ : ∀ x, ∀ y, y ≠ 0 -> f x y = x - y * Int.floor (x / y)) :
  f (3 / 8) (-(2 / 5)) = -(1 / 40) := sorry
