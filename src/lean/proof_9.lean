theorem implies_and_not_or (x y z w : Prop) : (x ∧ y ∧ ¬z) → (w ∨ x) := by
  intro h
  cases h with
  | intro hx hyz =>
    apply Or.inr
    exact hx