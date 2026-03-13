!Write by Yi,Wencai
!Date:2014.05.04
!To correct the coordinates of atoms from the result of caculations last time

program main
implicit none
real(kind=16) :: x,y,z,a,c,d,e
integer :: i,counter,b,io,nu,ntotal
INTEGER,ALLOCATABLE,DIMENSION(:)::ele_nu
character(len=67) :: ch
character(len=1) :: s
character(len=3) :: fi
LOGICAL::selective
INTEGER::counte_val_nu
LOGICAL::flag

selective=.FALSE.

call system("dos2unix POSCAR 2> /dev/null")

open(50,file="OUTCAR")
rewind(50)
open(51,file="POSCAR")
rewind(51)
open(100,file="POSCAR.tmp")
rewind(100)

read(51,"(A)",end=53)ch !title
write(100,"(A10)")ADJUSTL(TRIM(ch))

read(51,"(A67)",end=53)ch              ! SCALE
write(100,"(2x,f17.14)")1.00000000000000

read(51,"(A67)",end=53)ch  !lattice
write(100,"(A67)")ch
read(51,"(A67)",end=53)ch
write(100,"(A67)")ch
read(51,"(A67)",end=53)ch
write(100,"(A67)")ch

read(51,"(A67)",end=53)ch  ! element name
write(100,"(A67)")ch     

read(51,"(A67)",iostat = io)ch  !! element number
  IF(io /= 0 ) THEN
   WRITE(*,*)'The program can open POSCAR and read its data,please it,Good Luck!'
   STOP
  END IF
  nu = counte_val_nu(ch,flag)
  IF(ALLOCATED(ele_nu)) DEALLOCATE(ele_nu)
  ALLOCATE(ele_nu(nu)); ele_nu=''
  READ(ch,*)(ele_nu(i),i=1,nu)
  ntotal=SUM(ele_nu(:)) 
  write(100,"(A67)")ch     

read(51,"(A1)",iostat = io)s
  CALL uppercase(s)
  if(ADJUSTL(TRIM(s))=='S')then
      selective=.TRUE.
      write(100,"(A18)")"Selective dynamics"
  else
      selective=.FALSE. 
       BACKSPACE(1)
  end if
write(100,"(A9)")"Cartesian"

do
read(50,"(5x,A3)",end=52)fi
  if(fi == "f/i")then
    read (50,"(7x,A1)")fi                            !next
    write(*,*)" "
    write(*,'(A)',advance='no')"please input the correction factor: "
    read(*,*)a
        do b=1,ntotal
        read(50,"(5x,f9.6,1x,f9.6,1x,f9.6,4x,f9.6,3x,f9.6,3x,f9.6)")x,y,z,c,d,e
           if(c == 0.0)then
                if(selective)then
                write(100,"(5x,f9.6,5x,f9.6,5x,f9.6,4x,A1,4x,A1,4x,A1)")x,y,z,"F","F","F"
                else
                 write(100,"(5x,f9.6,5x,f9.6,5x,f9.6)")x,y,z
                end if
           else
                x=x+c*a
		y=y+d*a
		z=z+e*a
                if(selective)then
                 write(100,"(5x,f9.6,5x,f9.6,5x,f9.6,4x,A1,4x,A1,4x,A1)")x,y,z,"T","T","T"     
                else
                 write(100,"(5x,f9.6,5x,f9.6,5x,f9.6)")x,y,z 
                end if
           end if
        end do
    write(*,'(A)')"The correction is done, try to rerun VASP, Good Luck!"
    write(*,*)" "
      close(50)
      close(51)
      call system("mv "//Trim("POSCAR POSCAR-bak"))
      call system("mv "//Trim("POSCAR.tmp POSCAR"))
    stop
  end if
end do

52 close(50)
53 close(51)
end program main

SUBROUTINE uppercase(string)
!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
!> Purpose: Convert a string to its upper case.                 <!
!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
IMPLICIT NONE
CHARACTER(LEN=*),INTENT(INOUT)::string
INTEGER::loop_index
INTEGER::length
        length=LEN_TRIM(string)
        DO loop_index=1, length
                IF(LGE(string(loop_index:loop_index),'a').AND.&
                   (LLE(string(loop_index:loop_index),'z'))) THEN
                        string(loop_index:loop_index)=ACHAR(IACHAR(&
                                   string(loop_index:loop_index))-32)
                END IF
        END DO
END SUBROUTINE uppercase

INTEGER  FUNCTION counte_val_nu(val,flag)
!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
!> purpose: to count the numeber of val 
!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
IMPLICIT NONE
CHARACTER(LEN=*),INTENT(in)::val
CHARACTER(LEN=256),DIMENSION(500)::v
INTEGER::i,counte,io_stat
LOGICAL::flag

v='NULL'
flag=.FALSE.
counte=1
READ(val,*,IOSTAT=io_stat)(v(i),i=1,1000)
DO
  IF(ADJUSTL(TRIM(v(counte)))/='NULL') THEN
    counte=counte+1
    flag=.TRUE.
  ELSE
    EXIT
  END IF
END DO
counte_val_nu=counte-1
END FUNCTION counte_val_nu

