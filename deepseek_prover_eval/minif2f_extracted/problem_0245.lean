import Mathlib

open Real Nat Topology
open scoped BigOperators

theorem amc12a_2019_p21
  (z : ℂ)
  (h₀ : z = (1 + Complex.I) / Real.sqrt 2) :
  (∑ k in Finset.Icc 1 12, (z^(k^2))) * (∑ k in Finset.Icc 1 12, (1 / z^(k^2))) = 36 := sorry
