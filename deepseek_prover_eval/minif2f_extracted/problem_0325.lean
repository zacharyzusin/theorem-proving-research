import Mathlib

open Real Nat Topology
open scoped BigOperators

theorem amc12a_2010_p22
  (x : ℝ) :
  49 ≤ ∑ k in Finset.Icc (1:ℕ) 119, abs (↑k * x - 1) := sorry
