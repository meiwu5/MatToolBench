PROGRAM band
!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
!>purpose:use this to transfer EIGENVAL to band <!
!>author:Wencai Yi                              <!
!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
IMPLICIT NONE
INTEGER::i,j,m,nb,nk,nn,ispin,cnt
CHARACTER(LEN=256)::tmp
CHARACTER(LEN=10)::fermi_logo
CHARACTER::hse
REAL(KIND=8),ALLOCATABLE,DIMENSION(:,:)::kp
REAL(KIND=8),ALLOCATABLE,DIMENSION(:,:)::kpvalue
REAL(KIND=8),ALLOCATABLE,DIMENSION(:)::k
REAL(KIND=8),DIMENSION(3,3)::lattice,recipvector
REAL(KIND=8),DIMENSION(3)::kspc
REAL(KIND=8)::a,b,c,scal,volume
REAL(KIND=8)::w,paixu,paixuup,paixudn
REAL(KIND=8),ALLOCATABLE,DIMENSION(:,:)::eigup,eigdn,eig
CHARACTER(20) :: cFmt = '(f10.4,5x, ??f10.4)'
INTEGER::io_stat
INTEGER::vbml1,cbml1,cbband,vbband
REAL(KIND=8)::fermi,Pi,vbm1,cbm1,bandgap1
REAL(KIND=8)::GetInputReal

Pi=3.14159
cbm1=9999.999
vbm1=-9999.999
cbband=9999
vbband=9999
!!!!!!!!!!!!!!!!!! fermi level !!!!!!!!!!!!!!!!!!!!
WRITE(*,*)''
fermi = GetInputReal("Input Fermi level(Default: read from current OUTCAR):",0.0)
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


!!!!!!!!!!!!!!!!! end find fermi level !!!!!!!!!!!!!!!!!
WRITE(*,'(A)',ADVANCE='no')"Type yes for HSE band caculation(Default: no): "
READ(*,'(A)')hse
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

! CALCULATE THE ANGLE BETWEEN TWO THE LATTICE
  CALL cross(lattice(:,2)*scal,lattice(:,3)*scal,recipvector(:,1))
  CALL cross(lattice(:,3)*scal,lattice(:,1)*scal,recipvector(:,2))
  CALL cross(lattice(:,1)*scal,lattice(:,2)*scal,recipvector(:,3))
  volume=lattice(1,1)*(lattice(2,2)*lattice(3,3)-lattice(2,3)*lattice(3,2))&
        +lattice(1,2)*(lattice(2,3)*lattice(3,1)-lattice(2,1)*lattice(3,3))&
        +lattice(1,3)*(lattice(2,1)*lattice(3,2)-lattice(2,2)*lattice(3,1))
  volume=volume*scal**3
  recipvector(:,:)=(2*PI/volume)*recipvector(:,:)

!! read EIGENVAL
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

IF(ALLOCATED(eigup)) DEALLOCATE(eigup)
ALLOCATE(eigup(nk,nn));eigup=0.0000
IF(ALLOCATED(eigdn)) DEALLOCATE(eigdn)
ALLOCATE(eigdn(nk,nn));eigdn=0.0000
IF(ALLOCATED(eig)) DEALLOCATE(eig)
ALLOCATE(eig(nk,nn));eig=0.0000
IF(ALLOCATED(kp)) DEALLOCATE(kp)
ALLOCATE(kp(nk,3));kp=0.0000
IF(ALLOCATED(kpvalue)) DEALLOCATE(kpvalue)
ALLOCATE(kpvalue(nk,3));kpvalue=0.0000

WRITE( cFmt(11:13) , '(i3)' )nn
!write(*,*)"ss",cFmt

IF(ispin.eq.2) THEN
  OPEN(7,FILE='bandup.dat',ACTION='WRITE',STATUS='UNKNOWN')
  REWIND(7)
  OPEN(8,FILE='banddn.dat',ACTION='WRITE',STATUS='UNKNOWN')
  REWIND(8)
  cnt=0
    DO i=1,nk
      READ(4,*)
      READ(4,*) (kp(i,j),j=1,3),w
      IF(hse=='y'.AND.w > 0.000001) THEN
         DO j=1,nn
           READ(4,*)tmp
         END DO
     ELSE
      cnt=cnt+1
      kpvalue(cnt,:)=kp(i,:)
      DO  j=1,nn
        READ(4,*) tmp,eigup(cnt,j),eigdn(cnt,j)
      END DO
     END IF
    END DO
    eigup=eigup-fermi    !! fermi level
    eigdn=eigdn-fermi    !! fermi level
  !!!!!!!!!1 pai xu !!!!!!!!!!!!!
  DO i=1,cnt
   DO j= 1,nn-1
      DO m=j+1,nn
        IF(eigup(i,m)<eigup(i,j))then
            paixuup=eigup(i,j)
            eigup(i,j)=eigup(i,m)
            eigup(i,m)=paixuup
         END IF
        IF(eigdn(i,m)<eigdn(i,j))then
            paixudn=eigdn(i,j)
            eigdn(i,j)=eigdn(i,m)
            eigdn(i,m)=paixudn
         END IF
      END DO
   END DO
  END DO
   !!!!!!!!!! figure out the CBM VBM !!!!
  DO i=1,cnt
    DO j= 1,nn
        IF(eigup(i,j)>0.0 .AND. eigup(i,j)<cbm1 )THEN
           cbm1=eigup(i,j)
           cbml1=i
           cbband=j
        END IF
        IF(eigup(i,j) < 0.0 .AND. eigup(i,j)>vbm1 )THEN
           vbm1=eigup(i,j)
           vbml1=i
           vbband=j
        END IF
        IF(eigdn(i,j)>0.0 .AND. eigdn(i,j)<cbm1 )THEN
           cbm1=eigdn(i,j)
           cbml1=i
           cbband=j
        END IF
        IF(eigdn(i,j) < 0.0 .AND. eigdn(i,j)>vbm1 )THEN
           vbm1=eigdn(i,j)
           vbml1=i
          vbband=j
        END IF
   END DO
  END DO
  bandgap1=cbm1-vbm1
  WRITE(*,*)" "
  IF(bandgap1 > 0.08)THEN
  eigup=eigup-vbm1    !!!!!!!!!! coreect once more to set VBM=0 !!!! if it is semiconductor     
  eigdn=eigdn-vbm1    !!!!!!!!!! coreect once more to set VBM=0 !!!!
    WRITE(*,'(A43,I3,A2,f10.4,f10.4,f10.4,f10.4,A3)')"The maximum of the valence band was at kpoint ",vbband," :",kpvalue(vbml1,:),vbm1+fermi," eV"
    WRITE(*,'(A43,I3,A2,f10.4,f10.4,f10.4,f10.4,A3)')"The minimum of the conduction band was at kpoint",cbband," :",kpvalue(cbml1,:),cbm1+fermi," eV"
    IF(vbml1==cbml1)THEN
      WRITE(*,'(A32,f10.4)')"This produces a direct band gap:",bandgap1
    ELSE
      WRITE(*,'(A34,f10.4)')"This produces a indirect band gap: ",bandgap1
    END IF
  ELSE
    WRITE(*,*)"It may be a metal for no band gap, please check band.dat"
  END IF    
  !!!!!!!!!!!! k shi !!!!!!!!!!!!!
  !!!!!!!!!!!! k shi !!!!!!!!!!!!!
  IF(ALLOCATED(k)) DEALLOCATE(k)
  ALLOCATE(k(cnt));k=0.0000
  k(1)=0.0
   DO i=1,cnt-1
      kspc=kpvalue(i+1,:)-kpvalue(i,:)
      kspc=MATMUL(kspc,recipvector)
      k(i+1)=k(i)+sqrt(kspc(1)**2+kspc(2)**2+kspc(3)**2)
   END DO
 !!!!!!!!!! write value way 2 !!!!!!!!!!!!!!!!!!!!!!!!!!!!
  DO i=1,nn
   WRITE(7,'((f10.4,5x,f10.4))',IOSTAT=io_stat)k(1),eigup(1,i)
   WRITE(8,'((f10.4,5x,f10.4))',IOSTAT=io_stat)k(1),eigdn(1,i)
   DO j=2,cnt
     IF(k(j-1)==k(j))CYCLE
     WRITE(7,'((f10.4,5x,f10.4))',IOSTAT=io_stat)k(j),eigup(j,i)
     WRITE(8,'((f10.4,5x,f10.4))',IOSTAT=io_stat)k(j),eigdn(j,i)
   END DO
     WRITE(7,*)"&"
     WRITE(8,*)"&"
          WRITE(7,*)" "
          WRITE(8,*)" "
  END DO
  !!!!!!!!!!!!!!!!!! k line !!!!!!!!!!!!!!!!!!!!!!
  DO i=2,cnt-1
   IF(k(i)==k(i-1)) THEN
     WRITE(7,'((f10.4,5x,f10.4))',IOSTAT=io_stat)k(i),eigup(cnt,nn)
     WRITE(8,'((f10.4,5x,f10.4))',IOSTAT=io_stat)k(i),eigup(cnt,nn)
     WRITE(7,'((f10.4,5x,f10.4))',IOSTAT=io_stat)k(i),eigup(1,1)+1.5
     WRITE(8,'((f10.4,5x,f10.4))',IOSTAT=io_stat)k(i),eigdn(1,1)+1.5
     WRITE(7,*)"&"
     WRITE(8,*)"&"
     WRITE(7,*)" "
     WRITE(8,*)" "
   END IF
  END DO
  !!!!!!!!!!!!!!!!!!!! feimi level !!!!!!!!!!!!
     WRITE(7,'((f10.4,5x,f10.4))',IOSTAT=io_stat)k(1),0.0
     WRITE(8,'((f10.4,5x,f10.4))',IOSTAT=io_stat)k(1),0.0
     WRITE(7,'((f10.4,5x,f10.4))',IOSTAT=io_stat)k(cnt),0.0
     WRITE(8,'((f10.4,5x,f10.4))',IOSTAT=io_stat)k(cnt),0.0
     WRITE(7,*)"&"
     WRITE(8,*)"&"


     CLOSE(7)
     CLOSE(8)
ELSE
  OPEN(UNIT=219,FILE='band.dat',ACTION='WRITE',STATUS='UNKNOWN')
  REWIND(219)
  cnt=0
  DO i=1,nk
     READ(4,*)
     READ(4,*) (kp(i,j),j=1,3),w
     IF( hse =='y' .AND. w > 0.000001 )THEN
!     WRITE(*,*)"value of hse:", hse,cnt
         DO j=1,nn
           READ(4,*)tmp
         END DO
         CYCLE
     ELSE
      cnt=cnt+1
      kpvalue(cnt,:)=kp(i,:)
       DO j=1,nn
         READ(4,*) tmp,eig(cnt,j)
       END DO
     END IF
  END DO
  eig=eig-fermi
  !!!!!!!!!!!!!!!!!!!1 pai xu !!!!!!!!!!!
  DO i=1,cnt
    DO j= 1,nn-1
      DO m=j+1,nn
        IF(eig(i,m)<eig(i,j))THEN
            paixu=eig(i,j)
            eig(i,j)=eig(i,m)
            eig(i,m)=paixu
         END IF
      END DO
   END DO
  END DO
 !!!!!!!!!! figure out the CBM VBM !!!!
  DO i=1,cnt
    DO j= 1,nn
        IF(eig(i,j)>0.0 .AND. eig(i,j)<cbm1 )THEN 
           cbm1=eig(i,j)
           cbml1=i
           cbband=j
        END IF
        IF(eig(i,j) < 0.0 .AND. eig(i,j)>vbm1 )THEN 
           vbm1=eig(i,j)
           vbml1=i
           vbband=j
        END IF
   END DO
  END DO
  bandgap1=cbm1-vbm1
  WRITE(*,*)" "
  IF(bandgap1 > 0.08)THEN
  eig=eig-vbm1    !!!!!!!!!! coreect once more to set VBM=0 !!!! if it is semiconductor     
    WRITE(*,'(A43,I3,A2,f10.4,f10.4,f10.4,f10.4,A3)')"The maximum of the valence band was at kpoint ",vbband," :",kpvalue(vbml1,:),vbm1+fermi," eV"
    WRITE(*,'(A43,I3,A2,f10.4,f10.4,f10.4,f10.4,A3)')"The minimum of the conduction band was at kpoint",cbband," :",kpvalue(cbml1,:),cbm1+fermi," eV"
    IF(vbml1==cbml1)THEN
      WRITE(*,'(A32,f10.4)')"This produces a direct band gap:",bandgap1
    ELSE
      WRITE(*,'(A34,f10.4)')"This produces a indirect band gap: ",bandgap1
    END IF
  ELSE
    WRITE(*,*)"It may be a metal for no band gap, please check band.dat"
  END IF
  !!!!!!!!!!!! k shi !!!!!!!!!!!!!
  IF(ALLOCATED(k)) DEALLOCATE(k)
  ALLOCATE(k(cnt));k=0.0000
  k(1)=0.0
   DO i=1,cnt-1
      kspc=kpvalue(i+1,:)-kpvalue(i,:)
      kspc=MATMUL(kspc,recipvector)
      k(i+1)=k(i)+sqrt(kspc(1)**2+kspc(2)**2+kspc(3)**2)
   END DO
  !!!!!!!!!! write value way 2 !!!!!!!!!!!!!!!!!!!!!!!!!!!!
  DO i=1,nn
   WRITE(219,'((f10.4,5x,f10.4))',IOSTAT=io_stat)k(1),eig(1,i)
    DO j=2,cnt
     IF(k(j-1)==k(j))CYCLE
     WRITE(219,'((f10.4,5x,f10.4))',IOSTAT=io_stat)k(j),eig(j,i)
    END DO
      WRITE(219,*)"&"
      WRITE(219,*)" "
  END DO
 !!!!!!!!!!!!!!!!!! k line !!!!!!!!!!!!!!!!!!!!!!
  DO i=2,cnt-1
   IF(k(i)==k(i-1)) THEN
     WRITE(219,'((f10.4,5x,f10.4))',IOSTAT=io_stat)k(i),eig(cnt,nn)
     WRITE(219,'((f10.4,5x,f10.4))',IOSTAT=io_stat)k(i),eig(1,1)+1.5
     WRITE(219,*)"&"
     WRITE(219,*)" "
   END IF
  END DO
 !!!!!!!!!!!!!!!!!!!! feimi level !!!!!!!!!!!!
     WRITE(219,'((f10.4,5x,f10.4))',IOSTAT=io_stat)k(1),0.0
     WRITE(219,'((f10.4,5x,f10.4))',IOSTAT=io_stat)k(cnt),0.0
     WRITE(219,*)"&"

     CLOSE(219)
END IF
IF(ALLOCATED(eigup)) DEALLOCATE(eigup)
IF(ALLOCATED(eigdn)) DEALLOCATE(eigdn)
IF(ALLOCATED(eig)) DEALLOCATE(eig)
IF(ALLOCATED(k)) DEALLOCATE(k)
IF(ALLOCATED(kpvalue)) DEALLOCATE(kpvalue)
IF(ALLOCATED(kp)) DEALLOCATE(kp)
CLOSE(4)
WRITE(*,*)''
WRITE(*,'(A)')"Plotting Band Structure By Origin from band.dat! Here you get it!"
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

SUBROUTINE cross(x,y,z)
  IMPLICIT NONE
  REAL(8), INTENT(IN) :: x(3)
  REAL(8), INTENT(IN) :: y(3)
  REAL(8), INTENT(OUT) :: z(3)
  z(1)=x(2)*y(3)-x(3)*y(2)
  z(2)=x(3)*y(1)-x(1)*y(3)
  z(3)=x(1)*y(2)-x(2)*y(1)
  RETURN
END SUBROUTINE

