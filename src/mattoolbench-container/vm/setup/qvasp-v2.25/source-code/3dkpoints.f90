PROGRAM main
INTEGER::points,alpoints
REAL(KIND=16)::add,x,y,z,x1,y1,scal
INTEGER::i,j
CHARACTER(LEN=14)::title

WRITE(*,'(A)',ADVANCE='no')"Please input the center point (x,y): "
READ(*,*)x1,y1
WRITE(*,'(A)',ADVANCE='no')"Please input the length scale: "
READ(*,*)scal
WRITE(*,'(A)',ADVANCE='no')"How many points in each direction: "
READ(*,*)points

add=2*scal/(points)
alpoints=points*points+1
title="Kpoints for BZ"
z=0.0

OPEN(UNIT=114,FILE='KPOINTS',STATUS='UNKNOWN',ACTION='WRITE')
REWIND(114)
WRITE(114,'(A14)')title
WRITE(114,*)alpoints
WRITE(114,'(A3)')"rec"


x=x1-scal
DO i=1,points
   y=y1-scal
   DO j=1,points
     WRITE(114,'(1xf16.8,3xf16.8,3xf16.8,3xI1)')x,y,z,1
     y=y+add
   END DO
   x=x+add
END DO
     WRITE(114,'(1xf16.8,3xf16.8,3xf16.8,3xI1)')x,y,z,1


CLOSE(114)

WRITE(*,*)
WRITE(*,*)"Get the KPOINTS file in current folder!"
WRITE(*,*)

END PROGRAM main
