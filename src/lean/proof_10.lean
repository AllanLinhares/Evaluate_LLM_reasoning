theorem implies_and_comm (x y : Prop) : x ∧ y → y ∧ x := by
  intro h_xy
  cases h_xy with
  | intro hx hy =>
    exact And.intro hy hx