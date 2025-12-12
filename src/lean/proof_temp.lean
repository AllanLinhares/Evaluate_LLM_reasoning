theorem problem_proof (x y z w v : Prop) : (x ∧ (y ∨ ¬z)) → (w ∨ (v → x)) := by
  intro h
  cases h with
  | intro hx h_y_or_not_z =>
    apply Or.inr
    intro hv
    exact hx