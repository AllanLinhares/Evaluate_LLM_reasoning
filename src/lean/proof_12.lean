theorem xor_implies_or (x y : Prop) : (x ⊕ y) → (x ∨ y) := by
  intro h_xor
  cases h_xor with
  | inl h_and_not_y =>
    cases h_and_not_y with
    | intro hx hnoty =>
      exact Or.inl hx
  | inr h_not_x_and_y =>
    cases h_not_x_and_y with
    | intro hnotx hy =>
      exact Or.inr hy