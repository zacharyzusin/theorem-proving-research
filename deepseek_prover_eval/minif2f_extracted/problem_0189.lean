import Mathlib

open Real Nat Topology
open scoped BigOperators

theorem mathd_algebra_196
  (S : Finset ℝ)
  (h₀ : ∀ (x : ℝ), x ∈ S ↔ abs (2 - x) = 3) :
  ∑ k in S, k = 4 := sorry
