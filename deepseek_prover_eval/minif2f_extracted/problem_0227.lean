import Mathlib

open Real Nat Topology
open scoped BigOperators

theorem imo_2007_6
  (a : ℕ → NNReal)
  (h₀ : ∑ x in Finset.range 100, ((a (x + 1))^2) = 1) :
  ∑ x in Finset.range 99, ((a (x + 1))^2 * a (x + 2)) + (a 100)^2 * a 1 < 12 / 25 := sorry
