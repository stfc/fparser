module a_mod

   ! Access_Stmt
   private

   ! Attr_Spec with 0 and 1 additional attribute
   REAL, protected  :: planet_radius = 123
   REAL, parameter, protected  :: planet_radius_constant = 123

   LOGICAL :: public_protected = .FALSE.
   LOGICAL :: only_protected = .FALSE.
   LOGICAL :: private_protected = .FALSE.

   ! Access_stmt
   PUBLIC  :: public_protected
   ! Protected_Stmt
   PROTECTED :: public_protected, only_protected
   ! Access_stmt
   private :: private_protected

   type :: my_type
      ! Private_Components_Stmt
      private
      integer :: a, b
   contains
      private

   end type my_type

   ! Access_Spec
   type(my_type), private :: my_var

contains
   subroutine sub_a
   end subroutine sub_a
end module a_mod