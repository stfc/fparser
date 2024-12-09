MODULE a_mod
  REAL :: planet_radius = 123
  REAL, PARAMETER :: planet_radius_constant = 123
  LOGICAL :: public_protected = .FALSE.
  LOGICAL :: only_protected = .FALSE.
  LOGICAL :: private_protected = .FALSE.
  PUBLIC :: public_protected
  TYPE :: my_type
    INTEGER :: a, b
    CONTAINS
  END TYPE my_type
  TYPE(my_type), PUBLIC :: my_var
  CONTAINS
  SUBROUTINE sub_a
  END SUBROUTINE sub_a
END MODULE a_mod
