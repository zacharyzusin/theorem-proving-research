import Mathlib

open Real Nat Topology
open scoped BigOperators

theorem induction_sum_1oktkp1
  (n : ℕ) :
  ∑ k in (Finset.range n), (1 : ℝ) / ((k + 1) * (k + 2)) = n / (n + 1) := sorry
