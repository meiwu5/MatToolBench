MODULE tools
TYPE,PUBLIC::poscar
         CHARACTER(LEN=8)::poscar_title="qvasp"
         REAL(16),DIMENSION(3,3)::lattice
         CHARACTER(LEN=6),ALLOCATABLE,DIMENSION(:)::ele_type
         INTEGER,ALLOCATABLE,DIMENSION(:)::ele_nu
         REAL(16),ALLOCATABLE,DIMENSION(:,:)::pos
         LOGICAL,ALLOCATABLE,DIMENSION(:,:)::relax
END tyPE poscar

CONTAINS

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
counte=0
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

SUBROUTINE direct2cartesian(pos,lattice)
!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
!>purpose:transfer direct to cartesian coordination  <!
!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
IMPLICIT NONE
REAL(16),DIMENSION(:,:),INTENT(INOUT)::pos
REAL(16),DIMENSION(3,3),INTENT(IN)::lattice

pos=MATMUL(pos,lattice)

END SUBROUTINE direct2cartesian


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


SUBROUTINE cartesian2direct(pos,lattice)
!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
!>purpose:transfer cartesian to direct coordination <!
!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
IMPLICIT NONE
!INTEGER::all_nu
REAL(16),DIMENSION(:,:),INTENT(INOUT)::pos
REAL(16),DIMENSION(3,3),INTENT(IN)::lattice
REAL(16),DIMENSION(3,3)::latticeni
REAL(16)::val,tmp
LOGICAL::flag

latticeni=lattice

CALL  BRINV(latticeni,3,flag)  !!! this function come from tools
IF(.NOT.flag)THEN
 WRITE(*,*)"Please check the POSCAR or check tools.f90,or contact at yi.wencai@163.com!"
END IF

!write(*,*)latticeni
pos=MATMUL(pos,latticeni)

END SUBROUTINE cartesian2direct

SUBROUTINE read_poscar(infile,subs,flag_fedbak)
!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
!>purpose:read substrate information                  <!
!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
CHARACTER(LEN=*),INTENT(IN)::infile
TYPE(poscar)::subs
LOGICAL::f_exist=.FALSE.,flag=.FALSE.
LOGICAL,INTENT(OUT)::flag_fedbak
INTEGER::i,nu,io_stat
REAL(16)::scal
CHARACTER(LEN=128)::tmp
CHARACTER(LEN=18)::sele,coor_type

flag_fedbak=.FALSE.

INQUIRE(FILE=TRIM(ADJUSTL(infile)),EXIST=f_exist)
IF(.NOT.f_exist) THEN
 WRITE(*,'(A)') 'The poscar: "'//TRIM(ADJUSTL(infile))//'" do not exist,Please check it,Good Luck!'
 flag_fedbak=.FALSE.
 RETURN
END IF

OPEN(UNIT=202,FILE=TRIM(ADJUSTL(infile)),STATUS='OLD',ACTION='READ',IOSTAT=io_stat)
IF(io_stat /= 0 ) THEN
  WRITE(*,*)'The program can open "'//TRIM(ADJUSTL(infile))//'" and read its data,please it,Good Luck!'
  flag_fedbak=.FALSE.
  CLOSE(202)
  RETURN
END IF

REWIND(202)

READ(202,*,IOSTAT=io_stat)subs%poscar_title

IF(io_stat /= 0 ) THEN
  WRITE(*,*)'The program can open "'//TRIM(ADJUSTL(infile))//'" and read its data,please it,Good Luck!'
  flag_fedbak=.FALSE.
  CLOSE(202)
  RETURN
END IF

READ(202,*,IOSTAT=io_stat)scal
IF(io_stat /= 0 ) THEN
  WRITE(*,*)'The program can open "'//TRIM(ADJUSTL(infile))//'" and read its data,please it,Good Luck!'
  flag_fedbak=.FALSE.
  CLOSE(202)
  RETURN
END IF
lattic:DO i=1,3
  READ(202,*,IOSTAT=io_stat)subs%lattice(i,1),subs%lattice(i,2),subs%lattice(i,3)
  IF(io_stat /= 0 ) THEN
    WRITE(*,*)'The program can open "'//TRIM(ADJUSTL(infile))//'" and read its data,please it,Good Luck!'
    flag_fedbak=.FALSE.
    CLOSE(202)
    RETURN
  END IF
END DO lattic

subs%lattice=subs%lattice*scal
!! ele_type
READ(202,'(A)',IOSTAT=io_stat)tmp
IF(io_stat /= 0 ) THEN
  WRITE(*,*)'The program can open "'//TRIM(ADJUSTL(infile))//'" and read its data,please it,Good Luck!'
  flag_fedbak=.FALSE.
  CLOSE(202)
  RETURN
END IF
nu = counte_val_nu(tmp,flag)
IF(ALLOCATED(subs%ele_type)) DEALLOCATE(subs%ele_type)
ALLOCATE(subs%ele_type(nu)); subs%ele_type=''
READ(tmp,*)(subs%ele_type(i),i=1,nu)

!!ele_nu!!
READ(202,'(A)',IOSTAT=io_stat)tmp
IF(io_stat /= 0 ) THEN
  WRITE(*,*)'The program can open "'//TRIM(ADJUSTL(infile))//'" and read its data,please it,Good Luck!'
  flag_fedbak=.FALSE.
  CLOSE(202)
  RETURN
END IF
nu = counte_val_nu(tmp,flag)
IF(ALLOCATED(subs%ele_nu)) DEALLOCATE(subs%ele_nu)
ALLOCATE(subs%ele_nu(nu)); subs%ele_nu=0
READ(tmp,*)(subs%ele_nu(i),i=1,nu)


!!!! selective !!!
READ(202,*,IOSTAT=io_stat)sele
IF(io_stat /= 0 ) THEN
  WRITE(*,*)'The program can open "'//TRIM(ADJUSTL(infile))//'" and read its data,please it,Good Luck!'
  flag_fedbak=.FALSE.
  CLOSE(202)
  RETURN
END IF
CALL uppercase(sele)
IF(TRIM(ADJUSTL(sele(:1)))/='S')THEN
  BACKSPACE(202)
END IF

READ(202,*,IOSTAT=io_stat)coor_type
IF(io_stat /= 0 ) THEN
  WRITE(*,*)'The program can open "'//TRIM(ADJUSTL(infile))//'" and read its data,please it,Good Luck!'
  flag_fedbak=.FALSE.
  CLOSE(202)
  RETURN
END IF
CALL uppercase(coor_type)
IF(TRIM(ADJUSTL(coor_type(:1)))/='C'.AND.TRIM(ADJUSTL(coor_type(:1)))/='D')THEN
 WRITE(*,*)"The program can't figure out "//TRIM(ADJUSTL(infile))//'coordination type,Please check it and I will stop this program!'
 flag_fedbak=.FALSE.
 RETURN
END IF


IF(ALLOCATED(subs%pos)) DEALLOCATE(subs%pos)
ALLOCATE(subs%pos(SUM(subs%ele_nu),3)); subs%pos=0.0

IF(ALLOCATED(subs%relax)) DEALLOCATE(subs%relax)
ALLOCATE(subs%relax(SUM(subs%ele_nu),3)); subs%relax='T'

IF(TRIM(ADJUSTL(sele(:1)))=='S')THEN
  DO i=1,SUM(subs%ele_nu)
    READ(202,*,IOSTAT=io_stat)subs%pos(i,1),subs%pos(i,2),subs%pos(i,3),subs%relax(i,1),subs%relax(i,2),subs%relax(i,3)
    IF(io_stat /= 0 ) THEN
     WRITE(*,*)'The program can open "'//TRIM(ADJUSTL(infile))//'" and read its data,please it,Good Luck!'
      flag_fedbak=.FALSE.
      CLOSE(202)
     RETURN
     END IF
  END DO
ELSE
  DO i=1,SUM(subs%ele_nu)
  READ(202,*,IOSTAT=io_stat)subs%pos(i,1),subs%pos(i,2),subs%pos(i,3)
    IF(io_stat /= 0 ) THEN
    WRITE(*,*)'The program can open "'//TRIM(ADJUSTL(infile))//'" and read its data,please it,Good Luck!'
      flag_fedbak=.FALSE.
      CLOSE(202)
     RETURN
     END IF
  END DO
!         WRITE(*,*)"I will set all the relax T  T  T"
  subs%relax=.TRUE.
END IF

IF(TRIM(ADJUSTL(coor_type(:1)))=='C')THEN
 CALL cartesian2direct(subs%pos,subs%lattice)
END IF

  DO i=1,SUM(subs%ele_nu)
    subs%pos(i,1)=subs%pos(i,1)-REAL(FLOOR(subs%pos(i,1)))  ! normalization
    subs%pos(i,2)=subs%pos(i,2)-REAL(FLOOR(subs%pos(i,2)))
    subs%pos(i,3)=subs%pos(i,3)-REAL(FLOOR(subs%pos(i,3)))
  END DO

!CALL direct2cartesian(subs%pos,subs%lattice) ! tansfer to Cartesian coordinates

CLOSE(202)
flag_fedbak=.TRUE.
END SUBROUTINE read_poscar
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

SUBROUTINE write_poscar(pos1,infile)
!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
!>purpose: write poscar info in infile for 2d and interface
!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
IMPLICIT NONE
TYPE(poscar)::pos1
CHARACTER(LEN=*),INTENT(IN)::infile

!CHARACTER(LEN=EL),DIMENSION(SIZE(pos1%ele_type))::chos_ele
!INTEGER,DIMENSION(SIZE(pos1%ele_nu))::chos_ele_nu
!LOGICAL::choose
!INTEGER::vaild_ele_nu,vaild_ele_type_nu

INTEGER::i,j !,marknu,countnu
!write(*,*)"write poscar  ",pos1%pos(1,:)
!stop


OPEN(UNIT=203,FILE=TRIM(ADJUSTL(infile)),STATUS='UNKNOWN',ACTION='WRITE')
REWIND(203)
WRITE(203,'(A)')TRIM(ADJUSTL(pos1%poscar_title))
WRITE(203,'(A)')'1.00000000'
DO i=1,3
 WRITE(203,'(3F22.16)')pos1%lattice(i,:)
END DO
!WRITE(*,*)'write poscar',vaild_ele_nu
WRITE(203,*)TRIM(ADJUSTL(dimenchr2chr(pos1%ele_type,SIZE(pos1%ele_type(:)),SIZE(pos1%ele_type(:)))))
WRITE(203,*)TRIM(ADJUSTL(dimenint2chr(pos1%ele_nu,SIZE(pos1%ele_nu(:)),SIZE(pos1%ele_type(:)))))

IF(.NOT. ALL(pos1%relax(:,:)))THEN
 WRITE(203,'(A)')'Selective dynamics'
END IF

WRITE(203,'(A)')'Direct'
IF(.NOT. ALL(pos1%relax(:,:)))THEN
  DO i=1,SIZE(pos1%pos(:,3))
    WRITE(203,'(3F20.16,3L4)')pos1%pos(i,:),pos1%relax(i,:)
  END DO
ELSE
  DO i=1,SIZE(pos1%pos(:,3))
     WRITE(203,'(3F20.16,3L4)')pos1%pos(i,:) !pos1%relax(i,:)
  END DO
END IF
CLOSE(203)
!write(*,*)"countnu",countnu
!stop
!pos1%ele_type(1)="Du"
END SUBROUTINE write_poscar



END MODULE tools

PROGRAM switch_axis_main
!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
!> Purpose:  switch axis for POSCAR                             <!
!> Discription:                                                 <!
!> Note:                                                        <!
!> Record of revisions:                                         <!
!>   Date     Programmer  platform    Description of changes    <!
!> ========== ========== ========== ============================<!
!> 2024.06.29  Yi Wencai  Linux,i&g           None              <!   
!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
USE tools,ONLY:poscar,read_poscar,write_poscar
IMPLICIT NONE
REAL(KIND=16)::a,b,c,alpha,beta,gamm,tmp
TYPE(poscar)::subs
CHARACTER(LEN=100) infile,outfile
INTEGER::arg_count,swiax1,swiax2
LOGICAL::flag
INTEGER::i,j
!CHARACTER(LEN=80)::ch,filename,coordination,names,nuc
!CHARACTER(LEN=1)::selec

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

!!!!! read input file !!!!!!
CALL read_poscar(TRIM(ADJUSTL(infile)),subs,flag)
!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
a=SQRT(subs%lattice(1,1)**2+(subs%lattice(1,2))**2+(subs%lattice(1,3))**2)
b=SQRT((subs%lattice(2,1))**2+(subs%lattice(2,2))**2+(subs%lattice(2,3))**2)
c=SQRT((subs%lattice(3,1))**2+(subs%lattice(3,2))**2+(subs%lattice(3,3))**2)
!!!!!!!!!! alpha beta gamma !!!!!!!!!!
alpha=180.0/3.14159*ACOS((subs%lattice(2,1)*subs%lattice(3,1)+subs%lattice(2,2)*subs%lattice(3,2)+subs%lattice(2,3)*subs%lattice(3,3))/(b*c))
beta=180.0/3.14159*ACOS((subs%lattice(1,1)*subs%lattice(3,1)+subs%lattice(1,2)*subs%lattice(3,2)+subs%lattice(1,3)*subs%lattice(3,3))/(a*c))
gamm=180.0/3.14159*ACOS((subs%lattice(2,1)*subs%lattice(1,1)+subs%lattice(2,2)*subs%lattice(1,2)+subs%lattice(2,3)*subs%lattice(1,3))/(b*a))

!CALL write_poscar(subs,"out1.vasp")
!! alpha-->bc, beta-->ac gamm-->ab
!write(*,*)alpha,beta,gamm
!!!!!!! start switch axis !!!!!!!!!!
WRITE(*,*)
WRITE(*,*)"Input switch axis with two number [1-->a 2-->b 3-->c]:"
READ(*,*)swiax1,swiax2
!WRITE(*,*)swiax1,swiax2
!WRITE(*,*)subs%ele_nu
IF(swiax1==1.AND.swiax2==2)THEN
 tmp=a   !!! swith length
 a=b
 b=tmp
 tmp=alpha !!! swith angle
 alpha=beta
 beta=tmp
 DO i=1,SIZE(subs%pos(:,1))   !!! swith coordination
  tmp=subs%pos(i,1)
  subs%pos(i,1)=subs%pos(i,2)
  subs%pos(i,2)=tmp 
 END DO
 WRITE(*,*)"Switch a and b axis..."
 outfile="sw-ab.vasp"
ELSE IF(swiax1==1.AND.swiax2==3)THEN
 tmp=a   !!! swith length
 a=c
 c=tmp
 tmp=alpha !!! swith angle
 alpha=gamm
 gamm=tmp
 DO i=1,SIZE(subs%pos(:,1))   !!! swith coordination
  tmp=subs%pos(i,1)
  subs%pos(i,1)=subs%pos(i,3)
  subs%pos(i,3)=tmp
 END DO
 WRITE(*,*)"Switch a and c axis..."
 outfile="sw-ac.vasp"
ELSE IF(swiax1==2.AND.swiax2==1)THEN
 tmp=b   !!! swith length
 b=a
 a=tmp
 tmp=alpha !!! swith angle
 alpha=beta
 beta=tmp
 DO i=1,SIZE(subs%pos(:,1))   !!! swith coordination
  tmp=subs%pos(i,1)
  subs%pos(i,1)=subs%pos(i,2)
  subs%pos(i,2)=tmp
 END DO
 WRITE(*,*)"Switch a and b axis..."
 outfile="sw-ab.vasp"
ELSE IF(swiax1==2.AND.swiax2==3)THEN
 tmp=b   !!! swith length
 b=c
 c=tmp
 tmp=beta !!! swith angle
 beta=gamm
 gamm=tmp
 DO i=1,SIZE(subs%pos(:,1))   !!! swith coordination
  tmp=subs%pos(i,2)
  subs%pos(i,2)=subs%pos(i,3)
  subs%pos(i,3)=tmp
 END DO
 WRITE(*,*)"Switch b and c axis..."
 outfile="sw-bc.vasp"
ELSE IF(swiax1==3.AND.swiax2==1)THEN
 tmp=a   !!! swith length
 a=c
 c=tmp
 tmp=alpha !!! swith angle
 alpha=gamm
 gamm=tmp
 DO i=1,SIZE(subs%pos(:,1))   !!! swith coordination
  tmp=subs%pos(i,1)
  subs%pos(i,1)=subs%pos(i,3)
  subs%pos(i,3)=tmp
 END DO
 WRITE(*,*)"Switch a and c axis..."
 outfile="sw-ac.vasp"
ELSE IF(swiax1==3.AND.swiax2==2)THEN
 tmp=c   !!! swith length
 c=b
 b=tmp
 tmp=beta !!! swith angle
 beta=gamm
 gamm=tmp
 DO i=1,SIZE(subs%pos(:,1))   !!! swith coordination
  tmp=subs%pos(i,2)
  subs%pos(i,2)=subs%pos(i,3)
  subs%pos(i,3)=tmp
 END DO
 WRITE(*,*)"Switch b and c axis..."
 outfile="sw-bc.vasp"
ELSE
 WRITE(*,*)"Input the wrong switch axis number"
END IF

!write(*,*)alpha,beta,gamm
!!! recalculate the lattice
subs%lattice(1,1)=a
subs%lattice(1,2)=0
subs%lattice(1,3)=0
subs%lattice(2,1)=b*cosd(gamm)
subs%lattice(2,2)=b*sind(gamm)
subs%lattice(2,3)=0
subs%lattice(3,1)=c*cosd(beta)
subs%lattice(3,2)=c*(cosd(alpha)-cosd(gamm)*cosd(beta))/sind(gamm)
subs%lattice(3,3)=sqrt((c*sind(beta))**2-(subs%lattice(3,2))**2)

CALL write_poscar(subs,outfile)
WRITE(*,*)"Done, the result is written in "//TRIM(ADJUSTL(outfile))
WRITE(*,*)""

END PROGRAM switch_axis_main

