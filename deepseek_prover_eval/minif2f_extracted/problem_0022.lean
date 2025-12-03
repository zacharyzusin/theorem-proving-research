import Mathlib

open Real Nat Topology
open scoped BigOperators

theorem mathd_numbertheory_427
  (a : ℕ)
  (h₀ : a = (∑ k in (Nat.divisors 500), k)) :
  ∑ k in Finset.filter (λ x => Nat.Prime x) (Nat.divisors a), k = 25 := sorry
