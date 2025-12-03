import Mathlib

open Real Nat Topology
open scoped BigOperators

theorem mathd_algebra_206
  (a b : ℝ)
  (f : ℝ → ℝ)
  (h₀ : ∀ x, f x = x^2 + a * x + b)
  (h₁ : 2 * a ≠ b)
  (h₂ : f (2 * a) = 0)
  (h₃ : f b = 0) :
  a + b = -1 := sorry
