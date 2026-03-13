PROGRAM main
IMPLICIT NONE
REAL(KIND=16) x,y,z,mi,ma
INTEGER i,io_stat,nu,ntotal
CHARACTER(LEN=10) ch
CHARACTER(LEN=50) ele
CHARACTER(LEN=30) vaspfile
INTEGER,ALLOCATABLE,DIMENSION(:)::ele_nu
INTEGER::counte_val_nu
INTEGER::exsit
LOGICAL::flag

WRITE(*,*)' '

flag=.FALSE.

CALL SYSTEM("ls -l|awk '{print $NF}'|grep *.vasp"//Trim(" > dat"))
OPEN(221,FILE="dat")
READ(221,"(A30)",IOSTAT=exsit)vaspfile
CLOSE(221)
CALL SYSTEM("rm "//trim("dat"))
INQUIRE(FILE=TRIM(ADJUSTL(vaspfile)),EXIST=flag)
IF( .NOT. flag )THEN
   WRITE(*,'(A)',ADVANCE='no')" Please type input file name (in POSCAR format): "
   READ(*,'(A)')vaspfile
  INQUIRE(FILE=TRIM(ADJUSTL(vaspfile)),EXIST=flag)
  IF( .NOT. flag )THEN
    WRITE(*,*)'There is no' //ADJUSTL(TRIM(vaspfile))//' (from VESTA), please check it and reinput.'
    WRITE(*,*)' '
    STOP
  END IF
END IF

CALL SYSTEM("dos2unix "//ADJUSTL(TRIM(vaspfile))//" POSCAR 2> /dev/null")
call SYSTEM("cat "//ADJUSTL(TRIM(vaspfile))//" |sed -n '1,7p' > .xxx34322sx")

WRITE(*,'(A)',ADVANCE='no')" Input the Z coordinate interval you want to fix (eg: 0.1 0.2): "
READ(*,*)mi,ma

OPEN(1,FILE= vaspfile )
OPEN(2,ACCESS='Append',FILE=".xxx34322sx")
WRITE(2,"(A18)")"Selective dynamics"

REWIND(1)
DO i=1,6
  READ(1,*)ch
END DO
!! ele_type
READ(1,'(A)',IOSTAT=io_stat)ele
IF(io_stat /= 0 ) THEN
  WRITE(*,*)'The program can not open "'//TRIM(ADJUSTL(vaspfile))//'" and read its data,please it,Good Luck!'
  CLOSE(1)
  CLOSE(2)
  STOP
END IF
nu = counte_val_nu(ele,flag)
IF(ALLOCATED(ele_nu)) DEALLOCATE(ele_nu)
ALLOCATE(ele_nu(nu)); ele_nu=''
READ(ele,*)(ele_nu(i),i=1,nu)

ntotal=SUM(ele_nu(:))

READ(1,*)ch

CALL uppercase(ch)   !!! selective dynamics
IF(TRIM(ADJUSTL(ch(:1)))=='S')THEN
  READ(1,*)ch
END IF

WRITE(2,'(A)')ch
DO i=1,ntotal
 READ(1,*,IOSTAT=io_stat)x,y,z
 IF(io_stat /= 0 ) THEN
  WRITE(*,*)'The program can open "'//TRIM(ADJUSTL(vaspfile))//'" and read its data,please it,Good Luck!'
  CLOSE(1)
  CLOSE(2)
  STOP
 END IF
 IF(z > mi .AND. Z < ma)THEN
  WRITE(2,112)x,y,z,"F","F","F"
 ELSE
  WRITE(2,112)x,y,z,"T","T","T"
 END IF
109 FORMAT(3x,f13.9,7x,f13.9,7x,f13.9)
112 FORMAT(3x,f13.9,7x,f13.9,7x,f13.9,4x,A1,4x,A1,4x,A1)

END DO
50 CLOSE(1)

CALL SYSTEM("mv .xxx34322sx POSCAR 2> /dev/null")
WRITE(*,*)'Got it, check the POSCAR!'
WRITE(*,*)" "
CALL SYSTEM("dos2unix "//Trim("POSCAR 2> /dev/null"))
END PROGRAM main

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
