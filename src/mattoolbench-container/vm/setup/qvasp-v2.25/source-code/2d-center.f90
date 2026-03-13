PROGRAM twod_center_main
!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
!> Purpose:  Convert CONTCAR from VASP to out.cif for MS        <!
!> Discription:                                                 <!
!> Note:                                                        <!
!> Record of revisions:                                         <!
!>   Date     Programmer  platform    Description of changes    <!
!> ========== ========== ========== ============================<!
!> 2014.11.24  Yi Wencai  Linux,i&g           None              <!   
!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
IMPLICIT NONE
REAL(KIND=16)::c,layer_d
REAL(KIND=16)::scal
REAL(KIND=16),DIMENSION(3,3)::lattice
REAL(KIND=16),ALLOCATABLE,DIMENSION(:,:)::coordin
INTEGER,DIMENSION(111)::spe_nu
CHARACTER(LEN=2),DIMENSION(111)::nam
!INTEGER::f_exit_1,f_exit_2,f_exit_3,staus
INTEGER::arg_count,staus
LOGICAL::flag
INTEGER::i,j,columns,al
CHARACTER(LEN=80)::ch,infile,coordination,names,nuc,tmp

!!!!!!! input file !!!!!!!!!!!!!!!!
 arg_count=COMMAND_ARGUMENT_COUNT()
 SELECT CASE(arg_count)
  CASE(1)
    CALL get_command_argument(NUMBER=1,VALUE=infile)
  CASE DEFAULT
    infile='POSCAR' !! default value
  END SELECT

INQUIRE(FILE=TRIM(ADJUSTL(infile)),EXIST=flag)
IF( .NOT. flag )THEN
   WRITE(*,'(A)',ADVANCE='no')" Please type input file name (in POSCAR format):"
   READ(*,'(A)')infile
  INQUIRE(FILE=TRIM(ADJUSTL(infile)),EXIST=flag)
  IF( .NOT. flag )THEN
    WRITE(*,*)'There is no' //ADJUSTL(TRIM(infile))//' (from VESTA), please check it and reinput.'
    WRITE(*,*)' '
    STOP
  END IF
END IF
!WRITE(*,*)
!WRITE(*,*)"Transfer structure from "//ADJUSTL(TRIM(infile))//",Please waiting..."
OPEN(15,FILE=infile,ACTION="READ")
REWIND(15)

!!!!!!!! name scales lattice !!!!!!!!!
READ(15,*)ch
READ(15,*)scal
DO i=1,3
  READ(15,*)lattice(i,1),lattice(i,2),lattice(i,3)
END DO

lattice(:,:)=scal*lattice(:,:)
!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
c=SQRT((lattice(3,1))**2+(lattice(3,2))**2+(lattice(3,3))**2)

!!!!!!!!!!!!! the number and spceices of atom
READ(15,"(A80)")ch
READ(ch,*,IOSTAT=staus)(nam(j),j=1, 111)
READ(15,"(A80)")ch
READ(ch,*,IOSTAT=staus)(spe_nu(j),j=1, 111)

al=SUM(spe_nu(:))

IF(ALLOCATED(coordin)) DEALLOCATE(coordin)
ALLOCATE(coordin(al,3));coordin=0.0


columns=0
DO i=1,111
 IF ( spe_nu(i) /= 0 ) THEN
   columns=columns+1
 END IF
END DO

!!!!!!!!!!!! selective and coodination !!!!!!!
READ(15,*)ch
CALL ucase(ch)
IF ( ch(:1) /= "S" ) THEN
BACKSPACE(15)
END IF

READ(15,*)coordination
CALL ucase(coordination)

!!!!!!!!!!!!!!! x,y,z !!!!!!
DO i=1,al
   READ(15,*)coordin(i,1),coordin(i,2),coordin(i,3)
END DO

IF ( coordination(:1) == "C" ) THEN
  CALL ctod(coordin,lattice,al)
END IF

DO i=1,al
 coordin(i,3)=coordin(i,3)-FLOOR(coordin(i,3))
END DO

layer_d=(MAXVAL(coordin(:,3))+MINVAL(coordin(:,3)))/2.0
!write(*,*)"layer_d",layer_d

flag=.FALSE.
DO i=1,al
   IF (coordin(i,3) > layer_d-1.5/c .AND. coordin(i,3) < layer_d+1.5/c )THEN
     flag=.TRUE. 
   END IF
END DO

!write(*,*)"max",MAXVAL(coordin(:,3)),MINVAL(coordin(:,3))
IF (.NOT.flag)THEN
   layer_d=MAXVAL(coordin(:,3))-1.0+MINVAL(coordin(:,3))
   coordin(:,3)=coordin(:,3)-(layer_d)+0.5
   DO i=1,al
     coordin(i,3)=coordin(i,3)-FLOOR(coordin(i,3))
   END DO
   !!!!!!!!!!!!!!!!!!!!!! correct twice !!!!!!!!!!!
   layer_d=(MAXVAL(coordin(:,3))+MINVAL(coordin(:,3)))/2.0
!write(*,'(f10.6)')layer_d
   coordin(:,3)=coordin(:,3)-(layer_d)+0.5
END IF

OPEN(16,FILE="POSCAR_center",ACTION="WRITE")
REWIND(16)
WRITE(16,'(A5)')"qvasp"
WRITE(16,'(A5)')"1.000"
DO i=1,3
 WRITE(16,'(3f16.11)')lattice(i,1),lattice(i,2),lattice(i,3)
END DO
ch=""
DO i=1,columns
 ch=TRIM(ADJUSTL(ch))//' '//TRIM(ADJUSTL(nam(i)))
END DO
WRITE(16,*)TRIM(ADJUSTL(ch))

ch=""
DO i=1,columns
 WRITE(tmp,'(I4)')spe_nu(i)
 ch=TRIM(ADJUSTL(ch))//' '//TRIM(ADJUSTL(tmp))
END DO
WRITE(16,*)TRIM(ADJUSTL(ch))
WRITE(16,'(A6)')"Direct"
DO i=1,al
 WRITE(16,'(3F16.11)')coordin(i,1),coordin(i,2),coordin(i,3)
END DO
!!!!!!!!!!!!!! write data to out.cif !!!!!!!
CLOSE(15)
CLOSE(16)
END PROGRAM twod_center_main



SUBROUTINE ucase(string)
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
END SUBROUTINE ucase
SUBROUTINE ctod(coordin,lattice,al)
!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
! purpose: convert cartisen coodination to direct 
!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
INTEGER,INTENT(IN)::al
REAL(KIND=16),DIMENSION(al,3)::coordin
REAL(KIND=16),DIMENSION(3,3),INTENT(IN)::lattice
REAL(KIND=8),DIMENSION(3,3)::latticeni,a
REAL(KIND=8),DIMENSION(al,3)::cor,dir
INTEGER::i
REAL(KIND=8)::val
LOGICAL::flag
DO i=1,al
   cor(i,1)=coordin(i,1)
   cor(i,2)=coordin(i,2)
   cor(i,3)=coordin(i,3)
END DO

latticeni=lattice
CALL BRINV(latticeni,3,flag)
a=MATMUL(latticeni,lattice)

!WRITE(*,*)
!DO i=1,3
! WRITE(*,*)latticeni(i,:)
!END DO
dir=matmul(cor,latticeni)

DO i=1,al
  coordin(i,1)=dir(i,1)
  coordin(i,2)=dir(i,2)
  coordin(i,3)=dir(i,3)
END DO


END SUBROUTINE ctod

SUBROUTINE BRINV(A,N,flag)
IMPLICIT NONE
INTEGER,INTENT(IN)::N
REAL(KIND=8),DIMENSION(N,N),INTENT(INOUT)::A
REAL,DIMENSION(N)::IS,JS
REAL(KIND=8)::T,D
INTEGER::I,J,K
LOGICAL,INTENT(OUT)::flag

flag=.TRUE.

DO K=1,N
  D=0.0
  DO  I=K,N
   DO  J=K,N
    IF (ABS(A(I,J)).GT.D) THEN
      D=ABS(A(I,J))
      IS(K)=I
      JS(K)=J
    END IF
   END DO
  END DO

  IF (D+1.0.EQ.1.0) THEN
    flag=.FALSE.
    WRITE(*,"(1X,'ERR**NOT INV')")
    RETURN
  END IF

  DO J=1,N
    T=A(K,J)
    A(K,J)=A(IS(K),J)
    A(IS(K),J)=T
  END DO
  DO I=1,N
    T=A(I,K)
    A(I,K)=A(I,JS(K))
    A(I,JS(K))=T
   END DO
  A(K,K)=1/A(K,K)
  DO J=1,N
    IF (J.NE.K) THEN
      A(K,J)=A(K,J)*A(K,K)
    END IF
  END DO
  DO I=1,N
    IF (I.NE.K) THEN
      DO J=1,N
        IF (J.NE.K) THEN
          A(I,J)=A(I,J)-A(I,K)*A(K,J)
        END IF
      END DO
    END IF
  END DO
  DO I=1,N
    IF (I.NE.K) THEN
      A(I,K)=-A(I,K)*A(K,K)
    END IF
  END DO
END DO
DO K=N,1,-1
  DO J=1,N
    T=A(K,J)
    A(K,J)=A(JS(K),J)
    A(JS(K),J)=T
  END DO
  DO I=1,N
    T=A(I,K)
    A(I,K)=A(I,IS(K))
    A(I,IS(K))=T
  END DO
 END DO
RETURN
END SUBROUTINE BRINV
