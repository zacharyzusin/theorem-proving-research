import Mathlib

open Real Nat Topology
open scoped BigOperators

theorem mathd_numbertheory_32
  (S : Finset ℕ)
  (h₀ : ∀ (n : ℕ), n ∈ S ↔ n ∣ 36) :
  ∑ k in S, k = 91 := sorry
