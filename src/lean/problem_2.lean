theorem solver (x y : Prop) : x ∧ y → y ∧ x := by
  intro h
  cases h with
  | intro hx hy =>
    exact And.intro hy hx
