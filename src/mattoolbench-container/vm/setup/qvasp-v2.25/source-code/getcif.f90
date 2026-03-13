PROGRAM get_cif_main
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
REAL(KIND=16)::a,b,c,alpha,beta,gamm
REAL(KIND=16)::scal
REAL(KIND=16),DIMENSION(3,3)::lattice
REAL(KIND=16),ALLOCATABLE,DIMENSION(:,:)::coordin
INTEGER,DIMENSION(111)::spe_nu
CHARACTER(LEN=2),DIMENSION(111)::nam
!INTEGER::f_exit_1,f_exit_2,f_exit_3,staus
INTEGER::arg_count,staus
LOGICAL::flag
INTEGER::i,j,columns,al
CHARACTER(LEN=80)::ch,infile,coordination,names,nuc

!!!!!!! input file !!!!!!!!!!!!!!!!
 arg_count=COMMAND_ARGUMENT_COUNT()
 SELECT CASE(arg_count)
  CASE(1)
    CALL get_command_argument(NUMBER=1,VALUE=infile)
  CASE DEFAULT
    infile='CONTCAR' !! default value
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
WRITE(*,*)
WRITE(*,*)"Transfer structure from "//ADJUSTL(TRIM(infile))//",Pleasewaiting..."
OPEN(15,FILE=infile,ACTION="READ")
REWIND(15)

!!!!!!!! name scales lattice !!!!!!!!!
READ(15,*)ch
READ(15,*)scal
DO i=1,3
  READ(15,*)lattice(i,1),lattice(i,2),lattice(i,3)
END DO

!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
a=SQRT(lattice(1,1)**2+(lattice(1,2))**2+(lattice(1,3))**2)
b=SQRT((lattice(2,1))**2+(lattice(2,2))**2+(lattice(2,3))**2)
c=SQRT((lattice(3,1))**2+(lattice(3,2))**2+(lattice(3,3))**2)
!alpha=180.0/3.14159*ACOS((lattice(2,1)*lattice(3,1)+lattice(2,2)*lattice(3,2))/(b*c))
!beta=180.0/3.14159*ACOS(lattice(3,1)/c)
!gamm=180.0/3.14159*ACOS(lattice(2,1)/b)

!!!!!!!!!! alpha beta gamma !!!!!!!!!!
alpha=180.0/3.14159*ACOS((lattice(2,1)*lattice(3,1)+lattice(2,2)*lattice(3,2)+lattice(2,3)*lattice(3,3))/(b*c))
beta=180.0/3.14159*ACOS((lattice(1,1)*lattice(3,1)+lattice(1,2)*lattice(3,2)+lattice(1,3)*lattice(3,3))/(a*c))
gamm=180.0/3.14159*ACOS((lattice(2,1)*lattice(1,1)+lattice(2,2)*lattice(1,2)+lattice(2,3)*lattice(1,3))/(b*a))







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

IF ( coordination(:1) == "C" ) THEN
  CALL ctod(coordin,lattice,al)
END IF

!!!!!!!!!!!!!! write data to out.cif !!!!!!!
OPEN(38,FILE="out.cif",ACTION="WRITE",STATUS="REPLACE")
REWIND(38)
WRITE(38,"(A5)")"data_"
WRITE(38,"(A28)")"_audit_creation_method    ''"
WRITE(38,"(A25,f9.6)")"_cell_length_a           ",a
WRITE(38,"(A25,f9.6)")"_cell_length_b           ",b
WRITE(38,"(A25,f9.6)")"_cell_length_c           ",c
WRITE(38,"(A22,f8.4)")"_cell_angle_alpha     ",alpha
WRITE(38,"(A22,f8.4)")"_cell_angle_beta      ",beta
WRITE(38,"(A22,f8.4)")"_cell_angle_gamma     ",gamm
WRITE(38,"(A35)")"_symmetry_space_group_name_H-M  'T'"
WRITE(38,"(A5)")"loop_"
WRITE(38,"(A22)")"_atom_site_type_symbol"
WRITE(38,"(A16)")"_atom_site_label"
WRITE(38,"(A18)")"_atom_site_fract_x"
WRITE(38,"(A18)")"_atom_site_fract_y"
WRITE(38,"(A18)")"_atom_site_fract_z"
al=0
out2:DO i=1,columns
    inner2:DO j=1,spe_nu(i)
        al=al+1
        WRITE(nuc,*)al
        names= TRIM(nam(i)) // ADJUSTL(TRIM(nuc))
        WRITE(38,"(3X,A2,3X,A5,2X,F11.8,3X,F11.8,3X,F11.8)")TRIM(nam(i)),TRIM(names),coordin(al,1),coordin(al,2),coordin(al,3)
     END DO inner2
END DO out2

!!!!!!!!!!!!!!! Finished !!!!!!!!!
CALL SYSTEM("a=`pwd`;a=`basename $a`;mv out.cif $a.cif; echo Transfer it successfully!Please check $a.cif!")
!WRITE(*,*)"You have transfer it successfully!Please check out.cif!"
WRITE(*,*)""

!!!clean
IF(ALLOCATED(coordin)) DEALLOCATE(coordin)
CLOSE(15)
CLOSE(38)
END PROGRAM get_cif_main



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
