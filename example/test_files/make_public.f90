module a_mod

   ! Access_Stmt private will be removed:
   private

   ! Attr_Spec with 0 and 1 additional attribute, the protected will be remobed
   REAL, protected  :: planet_radius = 123
   REAL, parameter, protected  :: planet_radius_constant = 123

   LOGICAL :: public_protected = .FALSE.
   LOGICAL :: only_protected = .FALSE.
   LOGICAL :: private_protected = .FALSE.

   ! Access_stmt with public, this will be unmodified
   PUBLIC  :: public_protected
   ! Protected_Stmt - the whole statement will be removed
   PROTECTED :: public_protected, only_protected
   ! Access_stmt with private - the whole statement will be removed
   private :: private_protected

   type :: my_type
      ! Private_Components_Stmt in a type will be removed
      private
      integer :: a, b
   contains
      ! This private will also be removed.
      private

   end type my_type

   ! Access_Spec - the `private` will be removed
   type(my_type), private :: my_var

contains
   subroutine sub_a
   end subroutine sub_a
end module a_mod