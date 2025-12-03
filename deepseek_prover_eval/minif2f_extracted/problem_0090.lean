import Mathlib

open Real Nat Topology
open scoped BigOperators

theorem mathd_numbertheory_343 :
  (∏ k in Finset.range 6, (2 * k + 1)) % 10 = 5 := sorry
