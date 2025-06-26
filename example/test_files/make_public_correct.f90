MODULE a_mod

  ! Access_Stmt private will be removed:

  ! Attr_Spec with 0 and 1 additional attribute, the protected will be remobed
  REAL :: planet_radius = 123
  REAL, PARAMETER :: planet_radius_constant = 123

  LOGICAL :: public_protected = .FALSE.
  LOGICAL :: only_protected = .FALSE.
  LOGICAL :: private_protected = .FALSE.

  ! Access_stmt with public, this will be unmodified
  PUBLIC :: public_protected
  ! Protected_Stmt - the whole statement will be removed
  ! Access_stmt with private - the whole statement will be removed

  TYPE :: my_type
    ! Private_Components_Stmt in a type will be removed
    INTEGER :: a, b
    CONTAINS
    ! This private will also be removed.

  END TYPE my_type

  ! Access_Spec - the `private` will be removed
  TYPE(my_type), PUBLIC :: my_var

  CONTAINS
  SUBROUTINE sub_a
  END SUBROUTINE sub_a
END MODULE a_mod
