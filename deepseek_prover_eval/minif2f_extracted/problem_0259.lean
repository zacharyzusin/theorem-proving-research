import Mathlib

open Real Nat Topology
open scoped BigOperators

theorem mathd_numbertheory_149 :
  ∑ k in (Finset.filter (λ x => x % 8 = 5 ∧ x % 6 = 3) (Finset.range 50)), k = 66 := sorry
