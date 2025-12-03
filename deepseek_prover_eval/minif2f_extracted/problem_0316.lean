import Mathlib

open Real Nat Topology
open scoped BigOperators

theorem mathd_numbertheory_35
  (S : Finset ℕ)
  (h₀ : ∀ (n : ℕ), n ∣ (Nat.sqrt 196)) :
  ∑ k in S, k = 24 := sorry
