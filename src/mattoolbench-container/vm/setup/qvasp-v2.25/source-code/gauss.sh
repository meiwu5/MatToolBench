#!/bin/bash

#Write by : Yi,Wencai 
#Mail:yi.wencai@163.com
#Date:2014.06.21
#Modified by Yi,Wencai;2014.06.20
#Write it to transfer OUTCAR(from VASP) to Gauss log

 echo " "

if [ -f OUTCAR ]; then
     # scaling factor of forces
SCALING_FACTOR=1.0


# get input file name
if [ $# -eq 0 ]; then
    inp="OUTCAR"
else
    inp=$1
fi

# check existence of input file
if [ ! -f "$inp" ]; then
    echo Error: cannot find file "$inp".
    exit 1;
fi

awk -v scal=$SCALING_FACTOR '
BEGIN{
    ielem = 0;
    N = 0;        # total number of atoms
    flagUV = 0;
    iuv = 0;
    flagEN = 0;
    flagPos = 0;
    iat = 0;
    istep = 0;

    printf( " GradGradGradGradGradGradGradGradGradGradGradGradGradGradGradGradGradGrad\n");
}
{
    # get element types
    if( $0 ~ / VRHFIN =/ ){
        ix =  index($2,":");
        if( ix == 0 ){
            elem[ ielem ] = substr($2,2);
        }
        else{
            elem[ ielem ] = substr($2,2,ix-2);
        }
        ielem ++;
    }

    # get number of atoms for each element
    if( $0 ~ / ions per type = / ){
        for( i = 5; i <= NF; i ++ ){
            nat[i-5] = $i;
            N += nat[i-5];
        }
        # get array of element names
        ix = 0;
        for( j = 0; j < NF; j ++ ){
            for( i = 0; i < nat[j]; i ++ ){
                elemname[ix] = elem[ j ];
                ix ++;
            }
        }
    }

    # get components of unit vectors
    if( $0 ~ /direct lattice vectors/ ){
        flagUV = 1;
    }
    else if( flagUV && iuv < 3 ){
        uv[iuv, 0] = $1;
        uv[iuv, 1] = $2;
        uv[iuv, 2] = $3;
        iuv ++;
    }

    # get total energy
    if( $0 ~ /FREE ENERGIE OF THE ION-ELECTRON SYSTEM \(eV\)/ ){
        flagEN = 1;
    }
    ## DFT energy, if vdW forcefield is not included
    else if( flagEN == 1 && $0 ~ /energy\(sigma->0\)/ ){
        energy = $7;
        flagEN = 2;
    }
    ## DFT + vdW energy (total energy), if vdW forcefield is included
    else if( flagEN == 2 && $0 ~ /Estimated total energy \(eV\):/ ){
        energy = $5;
        flagEN = 0;
    }

    # get components of atom position vectors and forces
    if( $0 ~ /POSITION/ && $0 ~ /TOTAL-FORCE/ ){
        flagPos = 1;
    }
    else if( flagPos == 1 ){
        flagPos = 2;
    }
    else if( flagPos == 2 && iat < N ){
        xyz[iat, 0] = $1;
        xyz[iat, 1] = $2;
        xyz[iat, 2] = $3;
        force[iat, 0] = $4;
        force[iat, 1] = $5;
        force[iat, 2] = $6;
        maxf[iat] = force[iat, 0];
        maxf[iat] = force[iat, 1] > maxf[iat] ? force[iat, 1] : maxf[iat];
        maxf[iat] = force[iat, 2] > maxf[iat] ? force[iat, 2] : maxf[iat];
        fsum2[iat] = force[iat, 0]^2 + force[iat, 1]^2 + force[iat, 2]^2;
        iat ++;
    }
    else if( flagPos == 2 && iat == N ){
        # print out Coordinates
        printf( " GradGradGradGradGradGradGradGradGradGradGradGradGradGradGradGradGradGrad\n");
        printf( "                         Standard orientation:\n");
        printf( " ---------------------------------------------------------------------\n");
        printf( " Center     Atomic     Atomic              Coordinates (Angstroms)\n");
        printf( " Number     Number      Type              X           Y           Z\n");
        printf( " ---------------------------------------------------------------------\n");
        for( i = 0; i < N; i ++ ){
            printf( "%5i %10s %13i    %12.6f%12.6f%12.6f\n", i+1, elemname[i], 0, 
                    xyz[i,0], xyz[i,1], xyz[i,2]);
        }
        for( j = 0; j < 3; j ++ ){
            printf( "%5i %10s %13i    %12.6f%12.6f%12.6f\n", j+i+1, "Tv", 0, 
                    uv[j,0], uv[j,1], uv[j,2]);
        }
        printf( " ---------------------------------------------------------------------\n");

        # print out energy and forces
        printf( " SCF Done:  E =%16.8f     A.U.\n", energy );
        maxforce = maxf[0];
        rmsforce = fsum2[0];
        for( i = 1; i < N; i ++ ){
             maxforce = maxf[i] > maxforce ? maxf[i] : maxforce;
             rmsforce += fsum2[i];
        }
        rmsforce = ( rmsforce / N / 3 ) ^ 0.5;
        printf( " Cartesian Forces:  Max%16.9f RMS%16.9f\n", maxforce, rmsforce);

        # print out step number
        printf( " GradGradGradGradGradGradGradGradGradGradGradGradGradGradGradGradGradGrad\n");
        printf( " Step number%4i\n\n\n", istep+1);

        # print out force vectors
        printf( " GradGradGradGradGradGradGradGradGradGradGradGradGradGradGradGradGradGrad\n");
        printf( "                         Standard orientation:\n");
        printf( " ---------------------------------------------------------------------\n");
        printf( " Center     Atomic     Atomic              Coordinates (Angstroms)\n");
        printf( " Number     Number      Type              X           Y           Z\n");
        printf( " ---------------------------------------------------------------------\n");
        for( i = 0; i < N; i ++ ){
            printf( "%5i %10s %13i    %12.6f%12.6f%12.6f\n", i+1, elemname[i], 0, 
                    xyz[i,0], xyz[i,1], xyz[i,2]);
        }
        printf( " ---------------------------------------------------------------------\n");
        printf( "\n Harmonic frequencies (cm**-1), IR intensities (KM/Mole), Raman scattering\n" );
        printf( " activities (A**4/AMU), depolarization ratios for plane and unpolarized\n" );
        printf( " incident light, reduced masses (AMU), force constants (mDyne/A),\n" );
        printf( " and normal coordinates:\n" );
        printf( "%23i\n", 1 );
        printf( " Frequencies --%11.4f\n", maxforce );
        printf( " IR Inten    --%11.4f\n", rmsforce );
        printf( " Atom AN      X      Y      Z\n" );
        for( i = 0; i < N; i ++ ){
            printf( "%4i%4s  %7.2f%7.2f%7.2f\n", i+1, elemname[i], 
                force[i, 0]*scal, force[i, 1]*scal, force[i, 2]*scal );
        }
        printf( "\n -------------------\n");
        printf( "\n GradGradGradGradGradGradGradGradGradGradGradGradGradGradGradGradGradGrad\n");

        istep ++;
        iat = 0;
        flagPos = 0;
    }
}
END{
    printf( " GradGradGradGradGradGradGradGradGradGradGradGradGradGradGradGradGradGrad\n");
    printf( "\n Normal termination of Gaussian 03.\n" );
}
' "$inp" > VASP.log
echo "Got it, please use Gaussview open VASP.log" 
else 
 echo -e "Please confire that there exits OUTCAR in current folder\n"
fi

 echo " "
