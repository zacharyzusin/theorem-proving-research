import Mathlib

open Real Nat Topology
open scoped BigOperators

theorem mathd_numbertheory_461
  (n : ℕ)
  (h₀ : n = Finset.card (Finset.filter (λ x => Nat.gcd x 8 = 1) (Finset.Icc 1 7))) :
  (3^n) % 8 = 1 := sorry
