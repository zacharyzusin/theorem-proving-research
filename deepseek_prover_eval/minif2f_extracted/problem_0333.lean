import Mathlib

open Real Nat Topology
open scoped BigOperators

theorem mathd_algebra_405
  (S : Finset ℕ)
  (h₀ : ∀ x, x ∈ S ↔ 0 < x ∧ x^2 + 4 * x + 4 < 20) :
  S.card = 2 := sorry
