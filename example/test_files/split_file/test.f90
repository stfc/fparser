module mod1
  integer :: a
contains
  subroutine p(args)
    implicit none
    real :: args
        
  end subroutine p
end module mod1

subroutine sub()
end subroutine sub

real function func(args)
  use mod1
  func = 1    
end function func

program test_prog
  use mod1
end program test_prog

