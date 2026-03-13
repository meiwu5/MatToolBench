MODULE precise
!INTEGER, PARAMETER :: LP =SELECTED_REAL_KIND(p=14,r=400) !16
INTEGER, PARAMETER :: DP =SELECTED_REAL_KIND(p=14,r=200) !8
!INTEGER, PARAMETER :: MP =SELECTED_REAL_KIND(p=4,r=20)   !4
!INTEGER, PARAMETER :: SP =SELECTED_INT_KIND(4)           !2

INTEGER, PARAMETER :: EL =6  ! the length of elements

REAL(DP), PARAMETER :: MAX_BOND_LEN=1.7_DP ! key distance to judge top
REAL(DP), PARAMETER :: torlence=0.15_DP ! key distance to jude repeat
REAL(DP), PARAMETER :: bignum=99999.0_DP ! key distance to jude repeat
REAL(DP), PARAMETER :: smallnum=0.001_DP ! key distance to jude repeat

END MODULE precise

MODULE ele_info
!
!the data come from web: http://www.ccdc.cam.ac.uk/pages/Home.aspx
!
USE precise,ONLY:DP,EL
IMPLICIT NONE
INTEGER,PARAMETER::max_ele_nu=115     ! the last one is dumb atom,name: Du
CHARACTER(LEN=EL),DIMENSION(max_ele_nu)::ele
REAL(DP),SAVE,DIMENSION(max_ele_nu)::covalent_radii,atomic_radii,crystal_radii,ionic_radii,&
                         vdw_radii,ele_eng,ele_val,coord_max,coord_min
REAL(DP),SAVE,DIMENSION(max_ele_nu,max_ele_nu)::ljpotenialepsilon,ljpotenialc12,ljpotenialc6
! Lennard–Jones 

data ele/&
 'H',  'He', 'Li', 'Be', 'B',&
 'C',  'N',  'O',  'F',  'Ne',&
 'Na', 'Mg', 'Al', 'Si', 'P',&
 'S',  'Cl', 'Ar', 'K',  'Ca',&
 'Sc', 'Ti', 'V',  'Cr', 'Mn',&
 'Fe', 'Co', 'Ni', 'Cu', 'Zn',&
 'Ga', 'Ge', 'As', 'Se', 'Br',&
 'Kr', 'Rb', 'Sr', 'Y',  'Zr',&
 'Nb', 'Mo', 'Tc', 'Ru', 'Rh',&
 'Pd', 'Ag', 'Cd', 'In', 'Sn',&
 'Sb', 'Te', 'I',  'Xe', 'Cs',&
 'Ba', 'La', 'Ce', 'Pr', 'Nd',&
 'Pm', 'Sm', 'Eu', 'Gd', 'Tb',&
 'Dy', 'Ho', 'Er', 'Tm', 'Yb',&
 'Lu', 'Hf', 'Ta', 'W',  'Os',&
 'Re', 'Ir', 'Pt', 'Au', 'Hg',&
 'Tl', 'Pb', 'Bi', 'Po', 'At',&
 'Rn', 'Fr', 'Ra', 'Ac', 'Th',&
 'Pa', 'U',  'Np', 'Pu', 'Am',&
 'Cm', 'Bk', 'Cf', 'Es', 'Fm',&
 'Md', 'No', 'Lr', 'Rf', 'Db',&
 'Sg', 'Bh', 'Hs', 'Mt', 'Ds',&
 "H.5","H.75","H1.25","H1.5","H."/
DATA covalent_radii/&
 0.37_DP, 0.32_DP, 1.34_DP, 0.90_DP, 0.82_DP,& ! H  He Li Be B     
 0.77_DP, 0.75_DP, 0.73_DP, 0.71_DP, 0.69_DP,& ! C  N  O  F  Ne    
 1.54_DP, 1.30_DP, 1.18_DP, 1.11_DP, 1.06_DP,& ! Na Mg Al Si P 
 1.02_DP, 0.99_DP, 0.97_DP, 1.96_DP, 1.74_DP,& ! S  Cl Ar K  Ca
 1.44_DP, 1.36_DP, 1.25_DP, 1.27_DP, 1.39_DP,& ! Sc Ti V  Cr Mn
 1.25_DP, 1.26_DP, 1.21_DP, 1.38_DP, 1.31_DP,& ! Fe Co Ni Cu Zn
 1.26_DP, 1.22_DP, 1.19_DP, 1.16_DP, 1.14_DP,& ! Ga Ge As Se Br 
 1.10_DP, 2.11_DP, 1.92_DP, 1.62_DP, 1.48_DP,& ! Kr Rb Sr Y  Zr   
 1.37_DP, 1.45_DP, 1.56_DP, 1.26_DP, 1.35_DP,& ! Nb Mo Tc Ru Rh   
 1.31_DP, 1.53_DP, 1.48_DP, 1.44_DP, 1.41_DP,& ! Pd Ag Cd In Sn    
 1.38_DP, 1.35_DP, 1.33_DP, 1.30_DP, 2.25_DP,& ! Sb Te I  Xe Cs    
 1.98_DP, 1.69_DP, 1.69_DP, 1.69_DP, 1.69_DP,& ! Ba La Ce Pr Nd    
 1.69_DP, 1.69_DP, 1.69_DP, 1.69_DP, 1.69_DP,& ! Pm Sm Eu Gd Tb    
 1.69_DP, 1.69_DP, 1.69_DP, 1.69_DP, 1.69_DP,& ! Dy Ho Er Tm Yb    
 1.60_DP, 1.50_DP, 1.38_DP, 1.46_DP, 1.59_DP,& ! Lu Hf Ta W  Re    
 1.28_DP, 1.37_DP, 1.28_DP, 1.44_DP, 1.49_DP,& ! Os Ir Pt Au Hg    
 1.48_DP, 1.47_DP, 1.46_DP, 1.46_DP, 1.46_DP,& ! Tl Pb Bi Po At    
 1.45_DP, 1.45_DP, 1.45_DP, 1.45_DP, 1.45_DP,& ! Rn Fr Ra Ac Th    
 1.45_DP, 1.45_DP, 1.45_DP, 1.45_DP, 1.45_DP,& ! Pa U  Np Pu Am    
 1.45_DP, 1.45_DP, 1.45_DP, 1.45_DP, 1.45_DP,& ! Cm Bk Cf Es Fm    
 1.45_DP, 1.45_DP, 1.45_DP, 1.45_DP, 1.45_DP,& ! Md No Lr Rf Db    
 1.45_DP, 1.45_DP, 1.45_DP, 1.45_DP, 1.45_DP,& ! Sg Br Hs Mt Ds    
 0.37_DP, 0.37_DP, 0.37_DP, 0.37_DP, 0.37_DP/ ! H.5 H.75 H1.25 H1.5 H_s 

!atomic radii
DATA atomic_radii/&
 0.23_DP, 1.50_DP, 1.28_DP, 0.96_DP, 0.83_DP,& ! H  He Li Be B  
 0.68_DP, 0.68_DP, 0.68_DP, 0.64_DP, 1.50_DP,& ! C  N  O  F  Ne 
 1.66_DP, 1.41_DP, 1.21_DP, 1.20_DP, 1.05_DP,& ! Na Mg Al Si P  
 1.02_DP, 0.99_DP, 1.51_DP, 2.03_DP, 1.76_DP,& ! S  Cl Ar K  Ca 
 1.70_DP, 1.60_DP, 1.53_DP, 1.39_DP, 1.61_DP,& ! Sc Ti V  Cr Mn 
 1.52_DP, 1.26_DP, 1.24_DP, 1.32_DP, 1.22_DP,& ! Fe Co Ni Cu Zn 
 1.22_DP, 1.17_DP, 1.21_DP, 1.22_DP, 1.21_DP,& ! Ga Ge As Se Br 
 1.50_DP, 2.20_DP, 1.95_DP, 1.90_DP, 1.75_DP,& ! Kr Rb Sr Y  Zr 
 1.64_DP, 1.54_DP, 1.47_DP, 1.46_DP, 1.45_DP,& ! Nb Mo Tc Ru Rh 
 1.39_DP, 1.45_DP, 1.44_DP, 1.42_DP, 1.39_DP,& ! Pd Ag Cd In Sn 
 1.39_DP, 1.47_DP, 1.40_DP, 1.50_DP, 2.44_DP,& ! Sb Te I  Xe Cs 
 2.15_DP, 2.07_DP, 2.04_DP, 2.03_DP, 2.01_DP,& ! Ba La Ce Pr Nd 
 1.99_DP, 1.98_DP, 1.98_DP, 1.96_DP, 1.94_DP,& ! Pm Sm Eu Gd Tb 
 1.92_DP, 1.92_DP, 1.89_DP, 1.90_DP, 1.87_DP,& ! Dy Ho Er Tm Yb 
 1.87_DP, 1.75_DP, 1.70_DP, 1.62_DP, 1.51_DP,& ! Lu Hf Ta W  Re 
 1.44_DP, 1.41_DP, 1.36_DP, 1.50_DP, 1.32_DP,& ! Os Ir Pt Au Hg 
 1.45_DP, 1.46_DP, 1.48_DP, 1.40_DP, 1.21_DP,& ! Tl Pb Bi Po At 
 1.50_DP, 2.60_DP, 2.21_DP, 2.15_DP, 2.06_DP,& ! Rn Fr Ra Ac Th 
 2.00_DP, 1.96_DP, 1.90_DP, 1.87_DP, 1.80_DP,& ! Pa U  Np Pu Am 
 1.69_DP, 1.54_DP, 1.83_DP, 1.50_DP, 1.50_DP,& ! Cm Bk Cf Es Fm 
 1.50_DP, 1.50_DP, 1.50_DP, 1.50_DP, 1.50_DP,& ! Md No Lr Rf Db 
 1.50_DP, 1.50_DP, 1.50_DP, 1.50_DP, 1.50_DP,& ! Sg Br Hs Mt Ds 
 0.23_DP, 0.23_DP, 0.23_DP, 0.23_DP, 0.23_DP/ ! H.5 H.75 H1.25 H1.5 H_s

END MODULE ele_info


MODULE tools
USE precise,ONLY:EL,DP
IMPLICIT NONE

TYPE,PUBLIC::poscar
         CHARACTER(LEN=8)::poscar_title="GASCAP"
         REAL(DP),DIMENSION(3,3)::lattice
         CHARACTER(LEN=EL),ALLOCATABLE,DIMENSION(:)::ele_type
         INTEGER,ALLOCATABLE,DIMENSION(:)::ele_nu
         REAL(DP),ALLOCATABLE,DIMENSION(:,:)::pos
         LOGICAL,ALLOCATABLE,DIMENSION(:,:)::relax
END tyPE poscar
CONTAINS

SUBROUTINE find_ele_nu(ele_type,ele_line,n)
!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
!>purpose: find the ele number                <!
!>notes: we don't need to check ele_name,     <!
!>       because we check it when input       <!
!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
USE precise,ONLY:EL
USE ele_info,ONLY:ele,max_ele_nu
IMPLICIT NONE
INTEGER,INTENT(IN)::n
CHARACTER(LEN=EL),DIMENSION(n),INTENT(IN)::ele_type
INTEGER,DIMENSION(n),INTENT(OUT)::ele_line
INTEGER::t,i,j,k

DO i=1,n
    DO k=1,max_ele_nu
      IF (ele(k)==ele_type(i))THEN
         ele_line(i)=k
      END IF
    END DO
END DO

END SUBROUTINE find_ele_nu

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
REAL(DP),DIMENSION(:,:),INTENT(INOUT)::pos
REAL(DP),DIMENSION(3,3),INTENT(IN)::lattice

pos=MATMUL(pos,lattice)

END SUBROUTINE direct2cartesian

SUBROUTINE BRINV(A,N,flag)
!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
!>purpose: matrix inversion                                 <!
!          come from book write by Xu,Shiliang               !
!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
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

SUBROUTINE cartesian2direct(pos,lattice)
!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
!>purpose:transfer cartesian to direct coordination <!
!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
IMPLICIT NONE
!INTEGER::all_nu
REAL(DP),DIMENSION(:,:),INTENT(INOUT)::pos
REAL(DP),DIMENSION(3,3),INTENT(IN)::lattice
REAL(DP),DIMENSION(3,3)::latticeni
REAL(DP)::val,tmp
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
REAL(DP)::scal
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
ALLOCATE(subs%pos(SUM(subs%ele_nu),3)); subs%pos=0.0_DP

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

!!!!!!!!!!!!!!! check !!!!!!!!!!!!!!!!!!!!
!CALL check_ele(subs%ele_type,SIZE(subs%ele_type),flag_fedbak)
!IF (.NOT.flag_fedbak) THEN
!  WRITE(*,*)"The add_ele line exit unvaild value, Please check it! This error will kill program!"
!  RETURN
!END IF
!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
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

REAL(DP) FUNCTION distance(pos1,pos2)
!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
!>purpose:calculte the distance between pos1 and pos2      <!
!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
REAL(DP),DIMENSION(3),INTENT(IN)::pos1,pos2

distance=SQRT((pos1(1)-pos2(1))**2.0+(pos1(2)-pos2(2))**2.0+(pos1(3)-pos2(3))**2.0)

END FUNCTION distance

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

SUBROUTINE check_point(subs,top_atom,num)
USE precise,ONLY:MAX_BOND_LEN
IMPLICIT NONE
TYPE(poscar),INTENT(IN)::subs
INTEGER,INTENT(OUT)::num
!REAL(DP),ALLOCATABLE,DIMENSION(:,:)::adsorb_top
LOGICAL,DIMENSION(:)::top_atom
REAL(DP),DIMENSION(1,3)::try_point,pos_new
INTEGER::i,j,n,k !,coun
REAL(DP)::dis,a,b,c

DO i=1,SUM(subs%ele_nu)
  try_point(1,:)=subs%pos(i,:)
  !write(*,*)try_point(1,:)
  CALL direct2cartesian(try_point,subs%lattice)
  try_point(1,3)=try_point(1,3)+MAX_BOND_LEN
  !write(*,*)try_point(1,:)
!  coun=0
  DO j=1,SUM(subs%ele_nu)
    c=subs%pos(j,3)
    DO n=-1,1
     a=subs%pos(j,1)+n    !translational symmetry along a direction
     DO k=-1,1
      b=subs%pos(j,2)+k   !!translational symmetry along b direction
      pos_new(1,1)=a
      pos_new(1,2)=b
      pos_new(1,3)=c
      !write(*,*)pos_new(1,1)
      CALL direct2cartesian(pos_new,subs%lattice)
      !write(*,*)pos_new(1,1)
      dis=SQRT((pos_new(1,1)-try_point(1,1))**2.0+(pos_new(1,2)-try_point(1,2))**2.0+(pos_new(1,3)-try_point(1,3))**2.0) 
      !write(*,*)" "
      IF( dis<MAX_BOND_LEN*1.75 .AND. (try_point(1,3)-MAX_BOND_LEN*0.2)<pos_new(1,3) )THEN   ! above 0.5 angstron
        top_atom(i)=.FALSE.      ! the distance is smaller than 3.0 and the z of connecting atoms is larger than dummy atom
      END IF
      IF( dis<MAX_BOND_LEN*0.6 )THEN
         top_atom(i)=.FALSE.     ! the distance is smaller than 1.0
      END IF
  !write(*,*)coun,MAX_BOND_LEN
     END DO
    END DO
  END DO
END DO

num=0
DO i=1,SUM(subs%ele_nu)
  IF(top_atom(i))num=num+1
END DO


END SUBROUTINE check_point

SUBROUTINE voronoi(top_tmp,num,i,j,m,cycle_center,flag)
USE precise,ONLY:bignum,DP,smallnum
IMPLICIT NONE
INTEGER,INTENT(IN)::num,i,j,m
INTEGER::n
REAL(DP),DIMENSION(num,3),INTENT(IN)::top_tmp
REAL(DP),DIMENSION(3),INTENT(OUT)::cycle_center
LOGICAL,INTENT(OUT)::flag
REAL(DP)::a,b,c,A1,B1,C1,A2,B2,C2,radii,dis

flag=.FALSE.

a=SQRT((top_tmp(j,1)-top_tmp(m,1))**2.0+(top_tmp(j,2)-top_tmp(m,2))**2.0+(top_tmp(j,3)-top_tmp(m,3))**2.0)
b=SQRT((top_tmp(i,1)-top_tmp(m,1))**2.0+(top_tmp(i,2)-top_tmp(m,2))**2.0+(top_tmp(i,3)-top_tmp(m,3))**2.0)
c=SQRT((top_tmp(i,1)-top_tmp(j,1))**2.0+(top_tmp(i,2)-top_tmp(j,2))**2.0+(top_tmp(i,3)-top_tmp(j,3))**2.0)

 ! 计算外心坐标的方程组系数
    A1 = 2.0 * (top_tmp(j,1)-top_tmp(i,1))
    B1 = 2.0 * (top_tmp(j,2)-top_tmp(i,2))
    C1 = (top_tmp(j,1))**2 + (top_tmp(j,2))**2 - (top_tmp(i,1))**2 - top_tmp(i,2)**2

    A2 = 2.0 * (top_tmp(m,1)-top_tmp(j,1))
    B2 = 2.0 * (top_tmp(m,2)-top_tmp(j,2))
    C2 = (top_tmp(m,1))**2 + (top_tmp(m,2))**2 - (top_tmp(j,1))**2 -(top_tmp(j,2))**2

! 使用克拉默法则求解外心坐标   here is for 2D plane, for 3D space should be further improved
IF(ABS(A1 * B2 - A2 * B1)<smallnum)THEN
 flag=.FALSE.
 RETURN        ! the three point is linear, return flag=.FALSE.
END IF
cycle_center(1)= (C1 * B2 - C2 * B1) / (A1 * B2 - A2 * B1)
cycle_center(2)= (A1 * C2 - A2 * C1) / (A1 * B2 - A2 * B1)
cycle_center(3)=((top_tmp(i,3)+top_tmp(j,3)+top_tmp(m,3)))/3.0

!write(*,*)"cycle center",cycle_center(:)
radii=distance(cycle_center(:),top_tmp(i,:))

DO n=1,num
 IF(n==i)cycle   !! not judge three point of triangle
 IF(n==j)cycle
 IF(n==m)cycle
 !! for hexagonal,move 0.05 outside
 dis=SQRT((cycle_center(1)-top_tmp(n,1))**2.0+(cycle_center(2)-top_tmp(n,2))**2.0+(cycle_center(3)-top_tmp(n,3))**2.0)+0.05 
 IF(dis<radii)THEN   !!! only can use this for hexagon, can not use dis-radii < smallnum
   flag=.FALSE.
   RETURN
 END IF
END DO


flag=.TRUE.
!write(*,*)"i,j,m",i,j,m
!write(*,*)top_tmp(i,:)
!write(*,*)top_tmp(j,:)
!write(*,*)top_tmp(m,:)

!stop
END SUBROUTINE voronoi

SUBROUTINE get_adop_bri_hol(ele_top,lattice,top,bri,hol)
USE precise,ONLY:bignum,DP,EL
USE ele_info,ONLY:covalent_radii 
!!! funtion: get bridge sites and hollow sites via analysis top sites
!!! using Voronoi method
IMPLICIT NONE
CHARACTER(LEN=EL),DIMENSION(:),INTENT(IN)::ele_top
REAL(DP),ALLOCATABLE,DIMENSION(:,:),INTENT(IN)::top
REAL(DP),DIMENSION(3,3),INTENT(IN)::lattice
REAL(DP),ALLOCATABLE,DIMENSION(:,:),INTENT(OUT)::bri,hol
REAL(DP),DIMENSION(9*SIZE(top(:,1)),3)::top_tmp,top_cartesian
REAL(DP),DIMENSION(bignum,3)::bri_tmp,hol_tmp
CHARACTER(LEN=EL),DIMENSION(9*SIZE(top(:,1)))::ele_type
INTEGER,DIMENSION(9*SIZE(top(:,1)))::ele_line
REAL(DP),DIMENSION(1,3)::cycle_center,try_bri
INTEGER::i,j,m,n,num,coun_bri,coun_hol,mark
REAL(DP)::a,b,c,dis1,dis2
LOGICAL::flag,flag_bri

bri_tmp=bignum
hol_tmp=bignum
top_tmp=bignum
ele_type=" "
!! Constructing top site to cross periodic boundary condition along a and b direction
!write(*,*)ele_top
num=0
DO i=1,SIZE(top(:,1))
 c=top(i,3)
 DO j=-1,1
  a=top(i,1)+j
  !write(*,*)j
  DO m=-1,1
   b=top(i,2)+m
   num=num+1
   top_tmp(num,1)=a
   top_tmp(num,2)=b
   top_tmp(num,3)=c
   ele_type(num)=ele_top(i)
   !ele_line=
  END DO 
 END DO
END DO

top_cartesian(:,:)=top_tmp(:,:)
CALL find_ele_nu(ele_type,ele_line,num)
CALL direct2cartesian(top_cartesian,lattice)
!write(*,*)"all pos_tmp",num
!DO i=1,num
! write(*,*)i,top_tmp(i,:)
!END DO
!write(*,*)"top with peridic",num
!DO i=1,SIZE(top(:,1))
!  write(*,*)top_tmp(4*i,:)
!END DO
coun_hol=0
coun_bri=0
DO i=1,SIZE(top(:,1))  !judge inside of cell, not outside of cell
  mark=9*i-4
  DO j=1,num
    IF(j==mark)cycle
    DO m=1,num
      IF(m==j)cycle
      IF(m==mark)cycle
      !flag=.FALSE.
      CALL voronoi(top_cartesian,num,mark,j,m,cycle_center(1,:),flag)
      !IF(mark==5 .AND. j==14 .AND. m==32 )THEN
      !    write(*,*)flag
      !    write(*,*)cycle_center(1,:)
      !    stop
      !END IF
      IF(flag)THEN
       coun_hol=coun_hol+1
       CALL cartesian2direct(cycle_center,lattice)
       !!!!!!!!!!!!!!!add hol site for cycle center !!
!       write(*,*)9*i,j,m 
!       write(*,*)top_tmp(9*i,:)
!       write(*,*)top_tmp(j,:)
!       write(*,*)top_tmp(m,:)
       hol_tmp(coun_hol,:)=cycle_center(1,:)  
      END IF
    END DO
    !!!!!!!!!!!!! add bri site along chemical bonds !!!
    dis1=distance(top_cartesian(mark,:),top_cartesian(j,:))  !! two atom neighbor
    dis2=(covalent_radii(ele_line(mark))+covalent_radii(ele_line(j)))*1.2
    IF(dis1<dis2)THEN
      coun_bri=coun_bri+1
      bri_tmp(coun_bri,:)=(top_tmp(mark,:)+top_tmp(j,:))/2.0  
    END IF
  END DO
END DO

IF(ALLOCATED(bri)) DEALLOCATE(bri)
ALLOCATE(bri(coun_bri,3));
DO i=1,coun_bri
  bri(i,:)=bri_tmp(i,:)
END DO
IF(ALLOCATED(hol)) DEALLOCATE(hol)
ALLOCATE(hol(coun_hol,3));
DO i=1,coun_hol
  hol(i,:)=hol_tmp(i,:)
END DO


END SUBROUTINE get_adop_bri_hol

SUBROUTINE sort_ele(pos)
IMPLICIT NONE
REAL(DP),DIMENSION(:),INTENT(INOUT)::pos
REAL(DP)::temp
INTEGER::i,j,n

n=SIZE(pos(:))

DO i=1,n-1
  DO j=i+1,n
   IF (pos(i).GT.pos(j)) THEN
   temp = pos(i)
   pos(i) = pos(j)
   pos(j) = temp
   END IF
  END DO
END DO

END SUBROUTINE sort_ele

SUBROUTINE sort_center(pos)
IMPLICIT NONE
REAL(DP),DIMENSION(:,:),INTENT(INOUT)::pos
REAL(DP),DIMENSION(SIZE(pos(:,1)))::dis
REAL(DP)::temp1,temp2,temp3
INTEGER::i,j,n

n=SIZE(pos(:,1))
DO i=1,n
  pos(i,1)=pos(i,1)-FLOOR(pos(i,1))
  pos(i,2)=pos(i,2)-FLOOR(pos(i,2))
  dis(i)=SQRT((pos(i,1)-0.5)**2.0+(pos(i,2)-0.5)**2.0)
END DO

DO i=1,n-1
  DO j=i+1,n
   IF (dis(i).GT.dis(j)) THEN
     temp1 = pos(i,1)
     temp2 = pos(i,2)
     temp3 = pos(i,3)
     pos(i,:) = pos(j,:)
     pos(j,1) = temp1
     pos(j,2) = temp2
     pos(j,3) = temp3
     temp1 = dis(i)
     dis(i)=dis(j)
     dis(j)=temp1
   END IF
  END DO
END DO

END SUBROUTINE sort_center


SUBROUTINE whether_repeat(pos1,pos2,flag)
USE precise,ONLY:torlence
REAL(DP),DIMENSION(:),INTENT(IN)::pos1,pos2
INTEGER::i
LOGICAL,INTENT(OUT)::flag

flag=.TRUE.
DO i=1,SIZE(pos1(:))
  IF((pos1(i)-pos2(i))>torlence)THEN
     flag=.FALSE.
  END IF 
END DO

END SUBROUTINE whether_repeat

SUBROUTINE rm_repeat_point(subs,adsorb_pos,num)
USE precise,ONLY:torlence,bignum
IMPLICIT NONE
TYPE(poscar),INTENT(IN)::subs
REAL(DP),ALLOCATABLE,DIMENSION(:,:),INTENT(INOUT)::adsorb_pos
INTEGER,INTENT(IN)::num
REAL(DP),DIMENSION(num,SUM(subs%ele_nu))::pos_dis
LOGICAL,DIMENSION(SIZE(adsorb_pos(:,3)))::adsorb_flag
REAL(DP),DIMENSION(1,3)::try_point,subspos !,tran_vex
INTEGER::i,j,n,k,coun1,coun2
REAL(DP)::dis,minv,a,b,c
LOGICAL::flag1,flag2,flag

!! constucting distance maxtri
DO i=1,SIZE(adsorb_pos(:,3))
 try_point(1,:)=adsorb_pos(i,:)
 CALL direct2cartesian(try_point,subs%lattice)
 DO j=1,SUM(subs%ele_nu)
  c=subs%pos(j,3)                      !! should considering periodic boundary condition
  minv=bignum
  DO n=-1,1
   a=subs%pos(j,1)+n   ! along a direciton
   DO k=-1,1
     b=subs%pos(j,2)+k  ! along b direction
     subspos(1,1)=a
     subspos(1,2)=b
     subspos(1,3)=c
     CALL direct2cartesian(subspos,subs%lattice)
     dis=distance(subspos(1,:),try_point(1,:))
!SQRT((subspos(1,1)-try_point(1,1))**2.0+(subspos(1,2)-try_point(1,2))**2.0+(subspos(1,3)-try_point(1,3))**2.0)
     IF(dis<minv)THEN
       minv=dis     ! should chose minum dis
     END IF
   END DO
  END DO
  pos_dis(i,j)=minv
 END DO
END DO

!!!! sort data by element, to figurout elements !!!!!!!
DO i=1,SIZE(adsorb_pos(:,3))
coun1=0
 DO j=1,SIZE(subs%ele_nu)
   coun2=coun1+1
   coun1=coun1+subs%ele_nu(j)
   CALL sort_ele(pos_dis(i,coun2:coun1))
   !write(*,*)"ele_type",coun2,coun1,pos_dis(i,coun2:coun1)
 END DO
END DO

!write(*,*)"Constructing distance matrix:"
!DO i=1,SIZE(adsorb_pos(:,3))
!  write(*,*)pos_dis(i,:)
!END DO

adsorb_flag=.FALSE.
!!! perfer to use centre point !!!!!!!!!!!
try_point(1,1)=0.5_DP
try_point(1,2)=0.5_DP
try_point(1,3)=SUM(adsorb_pos(:,3))/num

!write(*,*)try_point(1,:)
!minv=bignum
!DO i=1,num
!  dis=distance(adsorb_pos(i,:),try_point(1,:))
!SQRT((adsorb_pos(i,1)-try_point(1,1))**2.0+(adsorb_pos(i,2)-try_point(1,2))**2.0+(adsorb_pos(i,3)-try_point(1,3))**2.0)
!  IF(dis<minv)THEN
!    minv=dis
!    coun1=i
!  END IF
!END DO
!adsorb_flag(coun1)=.TRUE.
adsorb_flag(1)=.TRUE.

!write(*,*)adsorb_flag
!adsorb_pos(coun,:)=new_adsorb_pos(coun,:)

!!!!!!!!!!! repeat point through translational symmetry  !!!!!
coun1=2  !!! inital
DO WHILE(coun1>1)
coun1=1
 DO i=1,num
  IF(adsorb_flag(i))THEN
   DO j=1,num
     IF(adsorb_flag(j))cycle   ! no need to test
     IF(j==i)cycle             ! no need to compare
     CALL whether_repeat(pos_dis(j,:),pos_dis(i,:),flag1) 
     IF(.NOT. flag1)THEN    ! step1: flag is false, pos(j,:) is not equal pos(i,:)
      DO n=1,num
       flag=.TRUE.
       IF(n==j)cycle
       IF(adsorb_flag(n))THEN
          CALL whether_repeat(pos_dis(j,:),pos_dis(n,:),flag2)  !! step2: whether pos(j,:) equal true family
          IF(flag2)THEN
             flag=.FALSE.
             exit
          END IF
       END IF
      END DO
     IF(flag)THEN
       adsorb_flag(j)=.TRUE.
!write(*,*)j," become true"
       coun1=coun1+1   !! welcome j joint the true family
     END IF
     END IF
   END DO
  END IF
 END DO
END DO

!write(*,*)"adsorb_flag",adsorb_flag
!!!! the point is too close (<1.0 angstrom)
DO i=1,num
 IF(adsorb_flag(i))THEN
  adsorb_pos(i,1)=adsorb_pos(i,1)-FLOOR(adsorb_pos(i,1))
  adsorb_pos(i,2)=adsorb_pos(i,2)-FLOOR(adsorb_pos(i,2))
  adsorb_pos(i,3)=adsorb_pos(i,3)-FLOOR(adsorb_pos(i,3))
  subspos(1,:)=adsorb_pos(i,:)
  CALL direct2cartesian(subspos,subs%lattice)
  DO j=1,num
   IF(.NOT.adsorb_flag(j))cycle
   IF(j==i)cycle
   try_point(1,1)=adsorb_pos(j,1)-FLOOR(adsorb_pos(j,1))
   try_point(1,2)=adsorb_pos(j,2)-FLOOR(adsorb_pos(j,2))
   try_point(1,3)=adsorb_pos(j,3)-FLOOR(adsorb_pos(j,3))
   CALL direct2cartesian(try_point,subs%lattice)
   dis=distance(subspos(1,:),try_point(1,:)) 
 !  write(*,*)dis
   IF(dis<1.0)THEN
     adsorb_flag(j)=.FALSE.
     adsorb_pos(i,:)=(adsorb_pos(i,:)+adsorb_pos(j,:))/2.0  ! average from those two point
   END IF
  END DO
 END IF
END DO

!!!!!!! marked the adsorb_flag(i)=.FALSE. with bignum !!
DO i=1,num
  IF(.NOT.adsorb_flag(i))THEN
     adsorb_pos(i,:)=bignum
  END IF
END DO
!write(*,*)"before"
!write(*,*)adsorb_flag
!!!!!!!!!!! repeat point through translational symmetry  !!!!!
!coun=2  !!! inital
!DO WHILE(coun>1)
!coun=1
! DO i=1,num
!   DO j=1,num
!    dis=SQRT((adsorb_pos(1,1)-new_adsorb_pos(1,1))**2.0+(adsorb_pos(1,2)-new_adsorb_pos(1,2))**2.0+(adsorb_pos(1,3)-new_adsorb_pos(1,3))**2.0)
!    write(*,*)dis,"distance"
!    IF( dis>0.01 .AND. ABS(adsorb_pos(j,1))<10)THEN  ! not same and not big number
!      tran_vex(1,:)=new_adsorb_pos(i,:)-adsorb_pos(j,:)
!      write(*,*)"tran_vex",i,j,tran_vex
!      DO m=1,SUM(subs%ele_nu)
!        new_pos(m,1)=subs%pos(m,1)+tran_vex(1,1)
!        new_pos(m,1)=new_pos(m,1)-REAL(FLOOR(new_pos(m,1)))  ! normalization refine
!        new_pos(m,2)=subs%pos(m,2)+tran_vex(1,2)
!        new_pos(m,2)=new_pos(m,2)-REAL(FLOOR(new_pos(m,2)))
!        new_pos(m,3)=subs%pos(m,3)+tran_vex(1,3)
!        new_pos(m,3)=new_pos(m,3)-REAL(FLOOR(new_pos(m,3)))
!       END DO  
!       subs%pos(:,:)=new_pos(:,:) 
!       CALL write_poscar(subs,"move")
!       stop
!       new_pos_flag=.FALSE.         !wether recover bak 
!       DO m=1,SUM(subs%ele_nu)  
!        try_point(1,:)=new_pos(m,:)
!        write(*,*)"try_point m",m,try_point(1,:)
!        CALL direct2cartesian(try_point,subs%lattice)
!        DO n=1,SUM(subs%ele_nu)
!         subspos(1,:)=subs%pos(n,:)
!         write(*,*)"subspos n",n,subspos(1,:)
!         CALL direct2cartesian(subspos,subs%lattice)
!         dis=SQRT((subspos(1,1)-try_point(1,1))**2.0+(subspos(1,2)-try_point(1,2))**2.0+(subspos(1,3)-try_point(1,3))**2.0)
!         write(*,*)"distance between subspos and try_point",m,n,dis
!         IF(dis<torlence)THEN
!           new_pos_flag(m)=.TRUE.
!           stop
!         END IF
!        END DO
!       END DO
!   END IF
!  END DO
!  write(*,*)"new_pos_flag",new_pos_flag
!           stop
!  IF(ALL(new_pos_flag))THEN
!    write(*,*)i,"sucess"
!    adsorb_pos(i,:)=new_adsorb_pos(i,:)
!    coun=coun+1
!  END IF
! END DO
!write(*,*)coun,"end"
!END DO

!DO i=1,num
!  write(*,*)adsorb_pos(i,:)
!END DO

END SUBROUTINE rm_repeat_point


END MODULE tools



PROGRAM MAIN
USE tools,ONLY:read_poscar,poscar,check_point,get_adop_bri_hol,rm_repeat_point,write_poscar,sort_center
USE precise,ONLY:DP,torlence,bignum,EL
IMPLICIT NONE
CHARACTER(LEN=256)::infile
LOGICAL::flag
TYPE(poscar)::subs
CHARACTER(LEN=EL),ALLOCATABLE,DIMENSION(:)::ele_line_top
INTEGER::arg_count,coun,num,i,j
LOGICAL,ALLOCATABLE,DIMENSION(:)::top_atom
REAL(DP),ALLOCATABLE,DIMENSION(:,:)::adsorb_top,adsorb_bri,adsorb_hol
REAL(DP),DIMENSION(bignum,3)::all_sites

 arg_count=COMMAND_ARGUMENT_COUNT()
 SELECT CASE(arg_count)
  CASE(1)
    CALL get_command_argument(NUMBER=1,VALUE=infile)
  CASE DEFAULT
    infile='POSCAR' !! default value
  END SELECT

CALL read_poscar(TRIM(ADJUSTL(infile)),subs,flag)  !! normalization, and transfer to Direct coordinates
IF(.NOT. flag)THEN
 WRITE(*,*)"Stop! wrong input file of "//TRIM(ADJUSTL(infile))
 STOP
END IF

IF(ALLOCATED(top_atom)) DEALLOCATE(top_atom)
ALLOCATE(top_atom(SUM(subs%ele_nu))); top_atom=.TRUE.
CALL check_point(subs,top_atom,num)  !check top position, and marked it as .FALSE. if the atom is not at top site

!write(*,*)num
 WRITE(*,*)"Analysis adsorption sites of "//TRIM(ADJUSTL(infile))//":"
!!!!!! get top position !!!
IF(ALLOCATED(adsorb_top)) DEALLOCATE(adsorb_top)
ALLOCATE(adsorb_top(num,3)); 
IF(ALLOCATED(ele_line_top)) DEALLOCATE(ele_line_top)
ALLOCATE(ele_line_top(num)); 
arg_count=0
coun=0
DO i=1,SIZE(subs%ele_nu)
  DO j=1,subs%ele_nu(i)
  coun=coun+1
  IF(top_atom(coun))THEN
   arg_count=arg_count+1
   adsorb_top(arg_count,:)=subs%pos(coun,:)
   ele_line_top(arg_count)=subs%ele_type(i) 
  END IF
 END DO
END DO
!write(*,*)"All top atoms are chosed for analysis:"
!DO i=1,num
!  write(*,*)adsorb_top(i,:),ele_line_top(i)
!END DO
!!!!!! get bridge and hollow position !!!
CALL get_adop_bri_hol(ele_line_top,subs%lattice,adsorb_top,adsorb_bri,adsorb_hol)
!DO i=1,SIZE(adsorb_hol(:,1))
! write(*,*)"hol",adsorb_hol(i,:)
!END DO
!num=SIZE(adsorb_top(:,1))
!DO i=1,num
!   write(*,*)adsorb_top(i,:)
!END DO
CALL sort_center(adsorb_top)
CALL sort_center(adsorb_bri)
CALL sort_center(adsorb_hol)
!write(*,*)"-------------"
!num=SIZE(adsorb_top(:,1))
!DO i=1,num
!   write(*,*)adsorb_top(i,:)
!END DO

coun=0
CALL rm_repeat_point(subs,adsorb_top,num)   ! remove repeat
!write(*,*)" "
write(*,*)"Top site(s): "
DO i=1,num
 IF(ABS(adsorb_top(i,1)-bignum)>torlence)THEN
   write(*,*)adsorb_top(i,:)
   coun=coun+1
   all_sites(coun,:)=adsorb_top(i,:)
 END IF
END DO


num=SIZE(adsorb_bri(:,1))
CALL rm_repeat_point(subs,adsorb_bri,num)   ! remove repeat
write(*,*)" "
write(*,*)"Bridge site(s): "
DO i=1,num
 IF(ABS(adsorb_bri(i,1)-bignum)>torlence)THEN
   write(*,*)adsorb_bri(i,:)
   coun=coun+1
   all_sites(coun,:)=adsorb_bri(i,:)
 END IF
END DO

num=SIZE(adsorb_hol(:,1))
!DO i=1,num
!   write(*,*)adsorb_hol(i,:)
!END DO
CALL rm_repeat_point(subs,adsorb_hol,num)   ! remove repeat
write(*,*)" "
write(*,*)"Hollow site(s): "
DO i=1,num
 IF(ABS(adsorb_hol(i,1)-bignum)>torlence)THEN
   write(*,*)adsorb_hol(i,:)
   coun=coun+1
   all_sites(coun,:)=adsorb_hol(i,:)
 END IF
END DO
write(*,*)" "

!write(*,*)"all site num",coun
CALL SYSTEM("rm -f .gascap.vasp 2> /dev/null")
CALL write_poscar(subs,".gascap.vasp")
OPEN(1181,file=".gascap.vasp",STATUS='old',POSITION= 'append')
WRITE(1181,'(I4)')coun
DO i=1,coun
 WRITE(1181,'(3F20.16,3L4)')all_sites(i,:)
END DO
CALL SYSTEM("mv .gascap.vasp "//TRIM(ADJUSTL(infile)))

END PROGRAM MAIN

