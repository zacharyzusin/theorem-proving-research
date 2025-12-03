import Mathlib

open Real Nat Topology
open scoped BigOperators

theorem algebra_amgm_prod1toneq1_sum1tongeqn
  (a : ℕ → NNReal)
  (n : ℕ)
  (h₀ : Finset.prod (Finset.range (n)) a = 1) :
  Finset.sum (Finset.range (n)) a ≥ n := sorry
