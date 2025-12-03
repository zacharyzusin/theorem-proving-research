import Mathlib

open Real Nat Topology
open scoped BigOperators

theorem numbertheory_2pownm1prime_nprime
  (n : ℕ)
  (h₀ : 0 < n)
  (h₁ : Nat.Prime (2^n - 1)) :
  Nat.Prime n := sorry
