import Mathlib

open Real Nat Topology
open scoped BigOperators

theorem mathd_numbertheory_64 :
  IsLeast {x : ℕ | 30 * x ≡ 42 [MOD 47]} 39 := sorry
