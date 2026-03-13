PROGRAM main
IMPLICIT NONE
REAL(KIND=8) x,y,z,mi,ma
INTEGER i,j,k,io_stat,im_nu,ntotal
CHARACTER(LEN=10) ch
INTEGER::counte_val_nu
INTEGER::exsit
LOGICAL::flag
CHARACTER(LEN=10)::int2chr

OPEN(1,FILE="POSCAR1",IOSTAT=exsit)
OPEN(2,FILE="POSCAR2",IOSTAT=exsit)
REWIND(1)
REWIND(2)
IF( exsit /=0 )THEN
  WRITE(*,*)"There is no POSCAR1 file, please check it and reinput."
  WRITE(*,*)' '
  STOP
END IF

CALL SYSTEM("dos2unix  POSCAR1 2> /dev/null")
CALL SYSTEM("dos2unix  POSCAR2 2> /dev/null")

OPEN(33,FILE="num")
REWIND(33)
READ(33,*)ntotal
READ(33,*)im_nu

WRITE(*,'(A)',ADVANCE='no')"Input the Z coordinate interval you want to fix (eg: 1.1 3.2): "
DO
READ(*,*,IOSTAT=exsit)mi,ma
IF( exsit /=0 )THEN
  WRITE(*,'(A)',ADVANCE='no')"Unvaild! reinput the Z coordinate interval you want to fix (eg: 0.1 0.2): "
ELSE
  EXIT;
END IF
END DO

DO i=0,im_nu-2
 call SYSTEM("cat POSCAR1 |sed -n '1,7p' > POSCAR")
 DO j=1,5
   READ(2,*)ch
 END DO
 OPEN(34,FILE="POSCAR",ACCESS='APPEND')
 WRITE(34,'(A)')"Selective Dynamics"
 WRITE(34,'(A)')"Cartesian"
 DO k=1,ntotal
   READ(2,*)ch,x,y,z
   IF(z > mi .AND. Z < ma)THEN
       WRITE(34,112)x,y,z,"F","F","F"
   ELSE
       WRITE(34,112)x,y,z,"T","T","T"
   END IF
 END DO 
 CLOSE(34)
 CALL SYSTEM("dos2unix "//Trim("POSCAR 2> /dev/null"))
 ch=int2chr(i)
 CALL SYSTEM("mkdir 0"//ADJUSTL(TRIM(ch))//" 2> /dev/null")   !! make new forlder
 CALL SYSTEM("mv POSCAR 0"//ADJUSTL(TRIM(ch)))   !! make new forlder
END DO

CLOSE(2)

109 FORMAT(3x,f13.9,7x,f13.9,7x,f13.9)
112 FORMAT(3x,f13.9,7x,f13.9,7x,f13.9,4x,A1,4x,A1,4x,A1)

50 CLOSE(1)

END PROGRAM main

CHARACTER(LEN=10) FUNCTION  int2chr(val)
!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
!>purpose:transfer integer to chacter          <!
!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
IMPLICIT NONE
INTEGER,INTENT(IN)::val
WRITE(int2chr,'(I10)')val
int2chr=TRIM(ADJUSTL(int2chr))
END FUNCTION int2chr
