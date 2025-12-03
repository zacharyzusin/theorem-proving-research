import Mathlib

open Real Nat Topology
open scoped BigOperators

theorem mathd_numbertheory_211 :
  Finset.card (Finset.filter (λ n => 6 ∣ (4 * ↑n - (2 : ℤ))) (Finset.range 60)) = 20 := sorry
