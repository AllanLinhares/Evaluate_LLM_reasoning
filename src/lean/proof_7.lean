theorem problem_proof (x y z v w : Prop) : (x ∧ (y ∨ ¬z)) → (w ∨ (v → x)) := by
  intro h_hyp
  apply Or.inr
  intro hv
  cases h_hyp with
  | intro hx _ =>
    exact hx