import Mathlib

open Real Nat Topology
open scoped BigOperators

theorem mathd_algebra_158
  (a : ℕ)
  (h₀ : Even a)
  (h₁ : ∑ k in Finset.range 8, (2 * k + 1) - ∑ k in Finset.range 5, (a + 2 * k) = (4:ℤ)) :
  a = 8 := sorry
