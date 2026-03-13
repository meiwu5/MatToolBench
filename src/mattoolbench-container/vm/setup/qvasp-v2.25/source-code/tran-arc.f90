PROGRAM tranarc
!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
!>purpose:use this to transfer EIGENVAL to band <!
!>author:Wencai Yi                              <!
!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
IMPLICIT NONE
INTEGER::i,j
CHARACTER(LEN=256)::tmp
REAL(KIND=8),DIMENSION(3,3)::lattice
REAL(KIND=8)::a,b,c,alpha,beta,gam
INTEGER::nu,io_stat
LOGICAL::flag
REAL(KIND=8),ALLOCATABLE,DIMENSION(:,:)::pos
CHARACTER(LEN=2),ALLOCATABLE,DIMENSION(:)::ele_type   !!! B N
INTEGER,ALLOCATABLE,DIMENSION(:)::ele_nu              !!! 3 3
CHARACTER(LEN=2),ALLOCATABLE,DIMENSION(:)::ele_pai   !!!  B B B N N N
INTEGER::counte_val_nu

! open CONTCAR
OPEN(UNIT=113,FILE='POSCAR',STATUS='OLD',ACTION='READ',IOSTAT=io_stat)
 IF(io_stat/=0)THEN
   WRITE(*,*)"I can't find POSCAR file here,Please check it!"
   STOP
 END IF
READ(113,*)tmp
READ(113,*)tmp
READ(113,*)tmp
READ(113,*)tmp
READ(113,*)tmp
!!! real elements from POSCAR
READ(113,'(A)',IOSTAT=io_stat)tmp
IF(io_stat /= 0 ) THEN
  CLOSE(113)
END IF
nu = counte_val_nu(tmp,flag)
IF(ALLOCATED(ele_type)) DEALLOCATE(ele_type)
ALLOCATE(ele_type(nu)); ele_type=''
READ(tmp,*)(ele_type(i),i=1,nu)

!!ele_nu!!
READ(113,'(A)',IOSTAT=io_stat)tmp
IF(io_stat /= 0 ) THEN
  CLOSE(113)
END IF
nu = counte_val_nu(tmp,flag)
IF(ALLOCATED(ele_nu)) DEALLOCATE(ele_nu)
ALLOCATE(ele_nu(nu)); ele_nu=0
READ(tmp,*)(ele_nu(i),i=1,nu)

nu=SUM(ele_nu(:))
IF(ALLOCATED(ele_pai)) DEALLOCATE(ele_pai)
ALLOCATE(ele_pai(nu)); ele_pai=''
IF(ALLOCATED(pos)) DEALLOCATE(pos)
ALLOCATE(pos(3,nu)); pos=0

nu=0
DO i=1,SIZE(ele_type(:))
 DO j=1,ele_nu(i)
    nu=nu+1
    ele_pai(nu)=ele_type(i)
 END DO
END DO
IF(ALLOCATED(ele_type)) DEALLOCATE(ele_type)
IF(ALLOCATED(ele_nu)) DEALLOCATE(ele_nu)
!write(*,*)ele_pai

!!!!!!!!!!!!!!!!! read OUTCAR  !!!!!!!
OPEN(UNIT=114,FILE='OUTCAR',STATUS='OLD',ACTION='READ',IOSTAT=io_stat)
OPEN(UNIT=115,FILE='md.arc',STATUS='REPLACE',ACTION='WRITE')
WRITE(115,'(A)')"!BIOSYM archive 3"
WRITE(115,'(A)')"PBC=ON"
 IF(io_stat/=0)THEN
   WRITE(*,*)"I can't find OUTCAR file here,Please check it!"
   STOP
 END IF
DO
READ(114,'(A35)',IOSTAT=io_stat)tmp
IF(io_stat/=0)EXIT
IF(TRIM(ADJUSTL(tmp))=='direct lattice vectors')THEN
  READ(114,*)lattice(1,1),lattice(1,2),lattice(1,3)
  READ(114,*)lattice(2,1),lattice(2,2),lattice(2,3)
  READ(114,*)lattice(3,1),lattice(3,2),lattice(3,3)
  a=SQRT(lattice(1,1)**2+lattice(1,2)**2+lattice(1,3)**2)             !a
  b=SQRT(lattice(2,1)**2+lattice(2,2)**2+lattice(2,3)**2)             !b
  c=SQRT(lattice(3,1)**2+lattice(3,2)**2+lattice(3,3)**2)             !c
  alpha=180.0/3.14159*ACOS((lattice(2,1)*lattice(3,1)+lattice(2,2)*lattice(3,2)+lattice(2,3)*lattice(3,3))/(b*c))   !alpha
  beta=180.0/3.14159*ACOS((lattice(1,1)*lattice(3,1)+lattice(1,2)*lattice(3,2)+lattice(1,3)*lattice(3,3))/(a*c))    !beta
  gam=180.0/3.14159*ACOS((lattice(2,1)*lattice(1,1)+lattice(2,2)*lattice(1,2)+lattice(2,3)*lattice(1,3))/(b*a))    !gamm
  !write(*,*)a,b,c
END IF
IF(TRIM(ADJUSTL(tmp))=='POSITION')THEN
  WRITE(115,'((74X,A6))')"0.0000"
  WRITE(115,'(A)')"!DATE     May 15 21:11:07 2019"
  WRITE(115,'((A3,1X,F8.3,1X,F8.3,1X,F8.3,1X,F8.3,1X,F8.3,1X,F8.3))')"PBC",a,b,c,alpha,beta,gam
READ(114,*)tmp
  DO i=1,nu
   READ(114,*)pos(1,i),pos(2,i),pos(3,i)
  WRITE(115,'(A2,3X,F15.9,F15.9,F15.9,1X,A4,1X,A1,6X,A2,6X,A2,2X,A5)')ele_pai(i),pos(1,i),pos(2,i),pos(3,i),'XXXX','1','xx',ele_pai(i),'0.000'
  END DO
WRITE(115,'(A3)')'end'
WRITE(115,'(A3)')'end'
END IF
END DO
WRITE(*,*)"Transfer done, see md.arc"
!END IF
IF(ALLOCATED(ele_pai)) DEALLOCATE(ele_pai)
IF(ALLOCATED(pos)) DEALLOCATE(pos)
END PROGRAM tranarc

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

