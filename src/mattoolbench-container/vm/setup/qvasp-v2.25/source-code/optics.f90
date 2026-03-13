PROGRAM MAIN
IMPLICIT NONE
REAL(KIND=16)::ener,x1,x2,y1,y2,z1,z2,xy1,xy2,yz1,yz2,zx1,zx2
REAL(KIND=16)::xx,yy,zz,xy,yz,zx
REAL(KIND=16)::pi,h,c,xishu
INTEGER::i

pi=3.141592654
!h=1.3806505E-23   ! J/K
h=6.62606957E-34   ! J*s
c=3.0E10           ! m/s
xishu=1.0E5

OPEN(FILE="REAL.dat",UNIT=111)
OPEN(FILE="IMAG.dat",UNIT=112)
OPEN(FILE="adsorptionsp.dat",UNIT=113)
!OPEN(FILE="b.dat",UNIT=114)
!OPEN(FILE="c.dat",UNIT=115)

write(113,*)"energy xx yy zz xy yz zx"
DO i=1,1000
 READ(111,*)ener,x1,y1,z1,xy1,yz1,zx1
 READ(112,*)ener,x2,y2,z2,xy2,yz2,zx2
 xx=4.0*pi*(ener*1.60217733E-19)/(h*c*xishu)*(((x1**2.0+x2**2.0)**0.5-x1)/2.0)**0.5
 yy=4.0*pi*(ener*1.60217733E-19)/(h*c*xishu)*(((y1**2.0+y2**2.0)**0.5-y1)/2.0)**0.5
 zz=4.0*pi*(ener*1.60217733E-19)/(h*c*xishu)*(((z1**2.0+z2**2.0)**0.5-z1)/2.0)**0.5
 xy=4.0*pi*(ener*1.60217733E-19)/(h*c*xishu)*(((xy1**2.0+xy2**2.0)**0.5-xy1)/2.0)**0.5
 yz=4.0*pi*(ener*1.60217733E-19)/(h*c*xishu)*(((yz1**2.0+yz2**2.0)**0.5-yz1)/2.0)**0.5
 zx=4.0*pi*(ener*1.60217733E-19)/(h*c*xishu)*(((zx1**2.0+zx2**2.0)**0.5-zx1)/2.0)**0.5
   WRITE(113,'(F15.8,1X,F15.8,1X,F15.8,1X,F15.8,1X,F15.8,1X,F15.8,1X,F15.8)')ener,xx,yy,zz,xy,yz,zx
! WRITE(113,*)ener,alpha
END DO
close(111)
close(112)
close(113)
!close(114)
!close(115)
END PROGRAM MAIN
