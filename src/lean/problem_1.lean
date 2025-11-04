theorem and_comm_rev (A B : Prop) (h : B ∧ A) : A ∧ B :=
  by
    cases h with hB hA
    split
    · exact hA
    · exact hB
