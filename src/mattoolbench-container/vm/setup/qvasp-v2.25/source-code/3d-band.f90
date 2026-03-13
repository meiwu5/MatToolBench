PROGRAM band
!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
!>purpose:use this to transfer EIGENVAL to band <!
!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
IMPLICIT NONE
INTEGER::i,j,nb,nk,nn,ispin,cnt
CHARACTER(LEN=256)::tmp
CHARACTER(LEN=10)::fermi_logo
CHARACTER::hse
REAL(KIND=8),ALLOCATABLE,DIMENSION(:,:)::kp
REAL(KIND=8),ALLOCATABLE,DIMENSION(:,:)::mesh
REAL(KIND=8)::w
REAL(KIND=8),ALLOCATABLE,DIMENSION(:,:)::eigup,eigdn,eig
CHARACTER(16) :: cFmt = '(i4,5x, ??f10.4)'
CHARACTER(16) :: cFmt_3 = '(1x, ??f10.4)'
INTEGER::io_stat
REAL(KIND=8)::fermi,scal,Pi,GetInputReal
INTEGER::fermi_sur,points,n
REAL(KIND=8),DIMENSION(3,3)::lattice
REAL(KIND=8)::a,b,c

Pi=3.14159

!!!!!!!!!!!!!!!!!! fermi level !!!!!!!!!!!!!!!!!!!!
WRITE(*,*)''
fermi = GetInputReal(" Input Fermi level(Default: read from current OUTCAR):",0.0)
IF(fermi==0.00)THEN
!open OUTCAR
OPEN(UNIT=114,FILE='OUTCAR',STATUS='OLD',ACTION='READ',IOSTAT=io_stat)
 IF(io_stat/=0)THEN
   WRITE(*,*)"I can't find OUTCAR file here,Please check it!"
   STOP
 END IF
DO
READ(114,'(A10)',IOSTAT=io_stat)fermi_logo
IF(io_stat/=0)EXIT
IF(TRIM(ADJUSTL(fermi_logo))=='E-fermi :')THEN
 BACKSPACE(114)
 READ(114,*)fermi_logo,tmp,fermi
END IF
END DO
END IF

WRITE(*,*)'Confirm Fermi Level:',fermi

hse='n'

WRITE(*,'(A)',ADVANCE='no')"Which band you want to plot(3D): "
READ(*,*)fermi_sur

OPEN(UNIT=4,FILE='EIGENVAL',STATUS='OLD',ACTION='READ',IOSTAT=io_stat)
IF(io_stat/=0)THEN
 WRITE(*,*)"I can't find EIGENVAL file here,Please check it!"
 STOP
END IF
REWIND(4)
READ(4,*)tmp,tmp,tmp,ispin
READ(4,*)tmp
READ(4,*)tmp
READ(4,*)tmp
READ(4,*)tmp
READ(4,*) nb,nk,nn

points=INT(SQRT(REAL(nk)))

IF(ALLOCATED(eigup)) DEALLOCATE(eigup)
ALLOCATE(eigup(nk,nn));eigup=0.0000
IF(ALLOCATED(eigdn)) DEALLOCATE(eigdn)
ALLOCATE(eigdn(nk,nn));eigdn=0.0000
IF(ALLOCATED(eig)) DEALLOCATE(eig)
ALLOCATE(eig(nk,nn));eig=0.0000
IF(ALLOCATED(kp)) DEALLOCATE(kp)
ALLOCATE(kp(nk,3));kp=0.000

IF(ALLOCATED(mesh)) DEALLOCATE(mesh)
ALLOCATE(mesh(points+1,points+1)); mesh=0.000

WRITE( cFmt(8:10) , '(i3)' )nn
WRITE( cFmt_3(5:7) , '(i3)' )points+1
IF(ispin.eq.2) THEN
  cnt=0
    DO i=1,nk
      READ(4,*)
      READ(4,*) (kp(i,j),j=1,3),w
      IF(hse=='y'.AND.w<0.000001)CYCLE
      cnt=cnt+1
      DO  j=1,nn
        READ(4,*) tmp,eigup(i,j),eigdn(i,j)
      END DO
    END DO
    eigup=eigup-fermi    !! fermi level
    eigdn=eigdn-fermi    !! fermi level
ELSE
  cnt=0
  DO i=1,nk
     READ(4,*)
     READ(4,*) (kp(i,j),j=1,3),w
     IF(hse=='y'.AND.w<0.000001)CYCLE
     cnt=cnt+1
     DO j=1,nn
        READ(4,*) tmp,eig(i,j)
     END DO
  END DO
eig=eig-fermi
END IF

!!!!!!!!!!!!!!!!! read a b c !!!!!!!!!!!!!!!!!!!
! open CONTCAR
OPEN(UNIT=113,FILE='CONTCAR',STATUS='OLD',ACTION='READ',IOSTAT=io_stat)
 IF(io_stat/=0)THEN
   WRITE(*,*)"I can't find CONTCAR file here,Please check it!"
   STOP
 END IF
READ(113,*)tmp
READ(113,*)scal
READ(113,*)lattice(1,1),lattice(1,2),lattice(1,3)
READ(113,*)lattice(2,1),lattice(2,2),lattice(2,3)
READ(113,*)lattice(3,1),lattice(3,2),lattice(3,3)
lattice(:,:)=scal*lattice(:,:)
a=SQRT(lattice(1,1)**2+lattice(1,2)**2+lattice(1,3)**2)             !a
b=SQRT(lattice(2,1)**2+lattice(2,2)**2+lattice(2,3)**2)             !b
c=SQRT(lattice(3,1)**2+lattice(3,2)**2+lattice(3,3)**2)             !c

!!!!!!!!!!!! k shi !!!!!!!!!!!!!
!     k(i)=k(i-1)+ABS((kpvalue(i,1)-kpvalue(i-1,1)))*2.0*Pi/a+ABS((kpvalue(i,2)-kpvalue(i-1,2)))*2.0*Pi/b&
!       +ABS((kpvalue(i,3)-kpvalue(i-1,3)))*2.0*Pi/c
!write(*,*)kp(3,1)
kp(:,1)=kp(:,1)*2.0*Pi/a
kp(:,2)=kp(:,2)*2.0*Pi/b
!write(*,*)kp(3,1)

DO i=1,points 
 mesh(1,i+1)=kp((points-1)*i+1,1)           !!! x fang xiang
 mesh(i+1,1)=kp(i,2)           !!! y fang xiang
END DO
!WRITE(*,*)points

n=0
DO i=2,points+1
 DO j=2,points+1
   n=n+1
   mesh(i,j)=eig(n,fermi_sur)
 END DO
END DO

IF(ispin.eq.2) THEN
 n=0
 DO i=2,points+1
  DO j=2,points+1
   n=n+1
   mesh(i,j)=eigup(n,fermi_sur)
  END DO
 END DO
 OPEN(88,FILE='3d-banddn.dat',ACTION='WRITE',STATUS='UNKNOWN')
 REWIND(88)
 DO i=1,points+1
  WRITE(88,cFmt_3,IOSTAT=io_stat)(mesh(i,j),j=1,points+1)
 END DO
 CLOSE(88)

 n=0
 DO i=2,points+1
  DO j=2,points+1
   n=n+1
   mesh(i,j)=eigup(n,fermi_sur)
  END DO
 END DO
 OPEN(88,FILE='3d-bandup.dat',ACTION='WRITE',STATUS='UNKNOWN')
 REWIND(88)
  DO i=1,points+1
  WRITE(88,cFmt_3,IOSTAT=io_stat)(mesh(i,j),j=1,points+1)
 END DO
 CLOSE(88)

ELSE
 n=0
 DO i=2,points+1
  DO j=2,points+1
    n=n+1
    mesh(i,j)=eig(n,fermi_sur)
  END DO
 END DO

 OPEN(88,FILE='3d-band.dat',ACTION='WRITE',STATUS='UNKNOWN')
 REWIND(88)
 DO i=1,points+1
  WRITE(88,cFmt_3,IOSTAT=io_stat)(mesh(i,j),j=1,points+1)
 END DO
 CLOSE(88)
END IF

IF(ALLOCATED(eigup)) DEALLOCATE(eigup)
IF(ALLOCATED(eigdn)) DEALLOCATE(eigdn)
IF(ALLOCATED(eig)) DEALLOCATE(eig)
IF(ALLOCATED(kp)) DEALLOCATE(kp)
IF(ALLOCATED(mesh)) DEALLOCATE(mesh)
CLOSE(4)
WRITE(*,'(A)')'The transfer finished,Please check the the band*.dat !Good Luck!'
WRITE(*,*)''
END PROGRAM band

REAL FUNCTION GetInputReal( cStr , rDef ) RESULT ( rOut )
CHARACTER( LEN = * ) , INTENT( IN ):: cStr
REAL , INTENT( IN ) :: rDef
REAL :: rR
INTEGER :: iErr
CHARACTER( LEN = 30 ) :: cRead
rOut = rDef
WRITE( * , '(a)' , ADVANCE = 'no' ) cStr
READ( * , '(a30)' ) cRead
IF ( Len_Trim( cRead ) <= 0 ) RETURN
READ( cRead , * , IOSTAT = iErr ) rR
IF ( iErr == 0 ) rOut = rR
END FUNCTION GetInputReal

