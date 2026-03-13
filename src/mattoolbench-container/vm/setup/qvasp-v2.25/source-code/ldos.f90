PROGRAM MAIN
IMPLICIT NONE
INTEGER::rank,line,filenu
INTEGER::i

OPEN(25,FILE=".tmp")
REWIND(25)
READ(25,*)rank
READ(25,*)line
READ(25,*)filenu
CLOSE(25)
!WRITE(*,*)rank,line,filenu
CALL calculate(rank,line,filenu)

END PROGRAM MAIN

SUBROUTINE calculate(rank,line,filenu)
IMPLICIT NONE
INTEGER::rank,line,filenu
CHARACTER(LEN=50),DIMENSION(filenu)::filename
REAL(KIND=16),DIMENSION(filenu,rank,line)::val,allval
character(11) :: cFmt = '(??(F13.7))'
INTEGER::i,j,t

allval=0.00
val=0.00
!!!!! read filename !
!!!!!!! qustion : how to judge the file fix my require !!!!!
OPEN(25,FILE=".tmp")
REWIND(25)
READ(25,*)rank
READ(25,*)line
READ(25,*)filenu

DO i=1,filenu
  READ(25,"(A50)")filename(i)
	OPEN(30,FILE=filename(i))
          REWIND(30)
	 inner: DO j=1,line
            READ(30,*)(val(i,t,j),t=1,rank)
            allval(1,:,j)=allval(1,:,j)+val(i,:,j)
	  END DO inner
          CLOSE(30)
!stop
END DO

!!!!!! WRITE THE VALUE #########
!!!!!!!!! format question !!!!!!!
OPEN(99,FILE="LDOS.dat",ACTION="WRITE")
REWIND(99)
!WRITE(99,*)(val(1,j),allval(i,j),i=2,rank,(j=1,line))
write( cFmt(2:3) , '(i2)' )rank
DO j=1,line
 WRITE(99,cFmt)val(1,1,j),(allval(1,i,j),i=2,rank)
END DO
CLOSE(99)


!WRITE(*,*)filename


END SUBROUTINE calculate
