import Mathlib

open Real Nat Topology
open scoped BigOperators

theorem mathd_numbertheory_155 :
  Finset.card (Finset.filter (λ x => x % 19 = 7) (Finset.Icc 100 999)) = 48 := sorry
