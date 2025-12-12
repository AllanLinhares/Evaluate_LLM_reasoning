theorem problem_proof (x y z w v : Prop) : (x ∧ (y ∨ ¬z)) → (w ∨ (v → x)) := by
  intro h_hyp
  apply Or.inr
  intro h_v
  exact h_hyp.left