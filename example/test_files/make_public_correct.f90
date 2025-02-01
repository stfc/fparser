MODULE a_mod

  ! Access_Stmt

  ! Attr_Spec with 0 and 1 additional attribute
  REAL :: planet_radius = 123
  REAL, PARAMETER :: planet_radius_constant = 123

  LOGICAL :: public_protected = .FALSE.
  LOGICAL :: only_protected = .FALSE.
  LOGICAL :: private_protected = .FALSE.

  ! Access_stmt
  PUBLIC :: public_protected
  ! Protected_Stmt
  ! Access_stmt

  TYPE :: my_type
    ! Private_Components_Stmt
    INTEGER :: a, b
    CONTAINS

  END TYPE my_type

  ! Access_Spec
  TYPE(my_type), PUBLIC :: my_var

  CONTAINS
  SUBROUTINE sub_a
  END SUBROUTINE sub_a
END MODULE a_mod
