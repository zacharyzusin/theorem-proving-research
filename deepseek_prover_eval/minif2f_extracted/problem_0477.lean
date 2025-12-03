import Mathlib

open Real Nat Topology
open scoped BigOperators

theorem mathd_numbertheory_412
  (x y : ℕ)
  (h₀ : x % 19 = 4)
  (h₁ : y % 19 = 7) :
  ((x + 1)^2 * (y + 5)^3) % 19 = 13 := sorry
