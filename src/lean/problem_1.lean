theorem and_commutativity_elim (h : B ∧ A) : A ∧ B :=
  by
    apply And.intro
    apply And.right at h
    exact h
    apply And.left at h
    exact h
