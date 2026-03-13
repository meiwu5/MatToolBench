PROGRAM plane_nanotube_main
!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
!> Purpose:  Convert POSCAR from VASP to POSCAR-nanotube        <!
!> Discription:                                                 <!
!> Note:                                                        <!
!> Record of revisions:                                         <!
!>   Date     Programmer  platform    Description of changes    <!
!> ========== ========== ========== ============================<!
!> 2014.11.24  Yi Wencai  Linux,i&g           None              <!   
!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
IMPLICIT NONE
REAL(KIND=16)::sita,r,pi,z_min,y_min,a,b,c,alpha,beta,gamm
REAL(KIND=16)::scal,det
REAL(KIND=16),DIMENSION(3,3)::lattice,a_diag,rot_matrix,temp
REAL(KIND=16),ALLOCATABLE,DIMENSION(:,:)::coordin
INTEGER,DIMENSION(111)::spe_nu
CHARACTER(LEN=2),DIMENSION(111)::nam
LOGICAL::flag
INTEGER::f_exit_2,arg_count,staus
INTEGER::i,j,columns,al,io_stat
REAL(KIND=16)::angle
CHARACTER(LEN=80)::ch,filename,coordination,names,nuc,infile
CHARACTER(LEN=256)::dimenchr2chr, dimenint2chr
pi=3.14159
!!!!!!! input file !!!!!!!!!!!!!!!!
 arg_count=COMMAND_ARGUMENT_COUNT()
 SELECT CASE(arg_count)
  CASE(1)
    CALL get_command_argument(NUMBER=1,VALUE=infile)
  CASE DEFAULT
    infile='POSCAR' !! default value
  END SELECT

OPEN(15,FILE=infile,ACTION="READ",IOSTAT=f_exit_2)
!follow judge by bash

IF (f_exit_2 == 0 ) THEN
  WRITE(*,'(A)')"You should know: "
  WRITE(*,'(A)')"         1.Roll along x direction;"
  WRITE(*,'(A)')"         2.Bending along Y direction to a cycle (360);"
  WRITE(*,'(A)')"         3.Vaccum layer direction along z direction for a 2D structue."
!   WRITE(*,*)""
!   WRITE(*,'(A)')"We will transfer  structure from ", infile, " Please waiting..."
ELSE
!   WRITE(*,*)""
   WRITE(*,'(A)')"There is no input file, STOP!"
!   WRITE(*,*)""
   STOP
END IF
REWIND(15)

WRITE(*,'(A)',ADVANCE='no')"Input the rolling angle from 0 to 360:"
READ(*,*)angle
!write(*,*)angle
!IF ( angle < 0 .OR. angle > 360) THEN
! WRITE(*,'(A)')"The input angle < 0 or > 360, STOP!"
! STOP
!END IF

!!!!!!!! name scales lattice !!!!!!!!!
READ(15,*)ch
READ(15,*)scal
DO i=1,3
  READ(15,*)lattice(i,1),lattice(i,2),lattice(i,3)
END DO

lattice=lattice*scal

a=SQRT(lattice(1,1)**2+(lattice(1,2))**2+(lattice(1,3))**2)
b=SQRT((lattice(2,1))**2+(lattice(2,2))**2+(lattice(2,3))**2)
c=SQRT((lattice(3,1))**2+(lattice(3,2))**2+(lattice(3,3))**2)
alpha=180.0/3.14159*ACOS((lattice(2,1)*lattice(3,1)+lattice(2,2)*lattice(3,2)+lattice(2,3)*lattice(3,3))/(b*c))
beta=180.0/3.14159*ACOS((lattice(1,1)*lattice(3,1)+lattice(1,2)*lattice(3,2)+lattice(1,3)*lattice(3,3))/(a*c))
gamm=180.0/3.14159*ACOS((lattice(2,1)*lattice(1,1)+lattice(2,2)*lattice(1,2)+lattice(2,3)*lattice(1,3))/(b*a))
r=SQRT((lattice(2,1))**2+(lattice(2,2))**2+(lattice(2,3))**2)/2.0/pi/(angle/360)


IF ( ABS(alpha-90.0) > 1 .OR. ABS(beta-90.0) > 1.0 .OR. ABS(gamm-90.0) > 1.0 )THEN
  WRITE(*,'(A)')"Require alpha=beta=gamm=90 (>89 or < 91),STOP"
  WRITE(*,'(A)')" "
  STOP
END IF


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
out:DO i=1,al
   READ(15,*)coordin(i,1),coordin(i,2),coordin(i,3)
END DO out


!!!!!!!!!!! diagonalize_lattice and coordination !!!!!!!!
a_diag=0.00
a_diag(1,1)=a
a_diag(2,2)=b
a_diag(3,3)=c
!temp(:,:)=lattice(:,:)
!write(*,*)"222",temp
!CALL  BRINV(temp,3,flag)
!IF(.NOT. flag)THEN
! WRITE(*,*)"THE LATTICE IS WRONG!"
! STOP
!END IF
!rot_matrix=MATMUL(a_diag,temp)

!coordin=MATMUL(coordin,rot_matrix)
lattice(:,:)=a_diag(:,:)
!write(*,*)"b",lattice(2,2)

IF ( coordination(:1) == "D" ) THEN
  coordin=MATMUL(coordin,lattice)   ! direct2cartesian
END IF


!!!!!!!!!! transfer to cycle !!!!!
!lattice(2,2)=r*8.0*angle/360
!lattice(3,3)=r*8.0*angle/360
z_min=(MINVAL(coordin(:,3))+MAXVAL(coordin(:,3)))/2
DO i=1,al
   sita=coordin(i,2)/r             !! transfer to cycle
   coordin(i,2)=(r+coordin(i,3)-z_min)*sin(sita)+2.0*r*angle/360
   coordin(i,3)=(r+coordin(i,3)-z_min)*cos(sita)+4.0*r*angle/360
END DO
y_min=MINVAL(coordin(:,2))-15 
z_min=MINVAL(coordin(:,3))-15
DO i=1,al
   coordin(i,2)=coordin(i,2)-y_min
   coordin(i,3)=coordin(i,3)-z_min
END DO
lattice(2,2)=MAXVAL(coordin(:,2))+15
lattice(3,3)=MAXVAL(coordin(:,3))+15
!!!!!!!!!!!!!! tou ying y and z !!!!!


!!!!!!!!!!!!!! write data to POSCAR-nanotube !!!!!!!
OPEN(38,FILE="POSCAR-nanotube",ACTION="WRITE",STATUS="REPLACE")
REWIND(38)
WRITE(38,"(A25)")"nantotube create by qvasp"
WRITE(38,"(F10.6)")1.00000000000
DO i=1,3
 WRITE(38,"(3F22.16)")lattice(i,1),lattice(i,2),lattice(i,3)
ENDDO
WRITE(38,*)TRIM(ADJUSTL(dimenchr2chr(nam,SIZE(nam(:)),columns)))
WRITE(38,*)TRIM(ADJUSTL(dimenint2chr(spe_nu,SIZE(spe_nu(:)),columns)))

WRITE(38,"(A9)")"Cartesian"
DO i=1,SUM(spe_nu(:))
     WRITE(38,"(3F22.16)")coordin(i,1),coordin(i,2),coordin(i,3)
END DO

!!!!!!!!!!!!!!! Finished !!!!!!!!!
WRITE(*,*)""
WRITE(*,'(A)')"Transfer it to Nanotube successfully!Please check POSCAR-nanotube!"
WRITE(*,*)""
WRITE(*,'(A)') "Cite with 'The calculations were assisted by the qvasp[1]'  "
WRITE(*,'(A)')"[1] Wencai Yi, et al.qvasp: A Flexible Toolkit for VASP Users in Materials Simulations"
WRITE(*,*)""

!!!clean
IF(ALLOCATED(coordin)) DEALLOCATE(coordin)
CLOSE(15)
CLOSE(38)
END PROGRAM plane_nanotube_main



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

END SUBROUTINE ctod

SUBROUTINE duijiao(lattice)
!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
! purpose: dui jiao hua lattice
!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
REAL(KIND=16),DIMENSION(3,3)::lattice

END SUBROUTINE duijiao 

CHARACTER(LEN=256) FUNCTION  dimenchr2chr(val,n1,n2)
!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
!>purpose:transfer dimension to chacter        <!
!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
IMPLICIT NONE
INTEGER,INTENT(IN)::n1,n2
CHARACTER(LEN=*),DIMENSION(n1),INTENT(IN)::val
INTEGER::i
dimenchr2chr=''
DO i=1,n2
dimenchr2chr=TRIM(ADJUSTL(dimenchr2chr))//' '//TRIM(ADJUSTL(val(i)))
END DO
END FUNCTION dimenchr2chr

CHARACTER(LEN=256) FUNCTION  dimenint2chr(val,n1,n2)
!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
!>purpose:transfer dimension to chacter        <!
!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
IMPLICIT NONE
INTEGER,INTENT(IN)::n1,n2
INTEGER,DIMENSION(n1),INTENT(IN)::val
INTEGER::i
CHARACTER(LEN=4)::tmp
dimenint2chr=''
DO i=1,n2
WRITE(tmp,'(I4)')val(i)
dimenint2chr=TRIM(ADJUSTL(dimenint2chr))//' '//TRIM(ADJUSTL(tmp))
END DO
END FUNCTION dimenint2chr

SUBROUTINE BRINV(A,N,flag)
!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
!>purpose: matrix inversion                                 <!
!          come from book write by Xu,Shiliang               !
!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
IMPLICIT NONE
INTEGER,INTENT(IN)::N
REAL(KIND=16),DIMENSION(N,N),INTENT(INOUT)::A
REAL,DIMENSION(N)::IS,JS
REAL(KIND=16)::T,D
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
