PROGRAM main

!!!!!!!!!!!!!!!!!!!!!!
!Write by: Yi,Wencai !
!Date:2014.06.20     !
!Updat:2022,01.02    !
!Write it for VASP   !
!!!!!!!!!!!!!!!!!!!!!!

IMPLICIT NONE
CHARACTER(LEN=30)::jobname="qvasp"
CHARACTER(LEN=35)::key=" "
CHARACTER(LEN=1000)::allkey=" "
CHARACTER(LEN=1000)::keywords=" "
INTEGER::arg_count=0          !commond line input argument count
INTEGER::i

arg_count=COMMAND_ARGUMENT_COUNT()
IF(arg_count/=0)THEN
 DO i=1,arg_count
  CALL GET_COMMAND_ARGUMENT(NUMBER=i,VALUE=key)
   allkey=TRIM(ADJUSTL(allkey))//' '//TRIM(ADJUSTL(key))
   IF(i>1)THEN
    keywords=TRIM(ADJUSTL(keywords))//' '//TRIM(ADJUSTL(key))
   END IF
 END DO
   CALL GET_COMMAND_ARGUMENT(NUMBER=1,VALUE=key)
 IF(arg_count==2)THEN
   CALL GET_COMMAND_ARGUMENT(NUMBER=2,VALUE=jobname)
 END IF
END IF

!######################## Job Control #################################
IF(arg_count==0)THEN
  CALL SYSTEM('bash $qvasppath/exefile/Tools/showstatus.sh')
  STOP
END IF
IF ( TRIM(ADJUSTL(key)) == "-d" ) THEN
  CALL SYSTEM('$qvasppath/exefile/Tools/qdel.sh '//TRIM(ADJUSTL(allkey)))
ELSE IF ( TRIM(ADJUSTL(key)) == "-sub" ) THEN
  CALL SYSTEM('$qvasppath/exefile/Tools/submit.sh '//TRIM(ADJUSTL(allkey)))
!########################### INCAR #################################
ELSE IF ( TRIM(ADJUSTL(key)) == "-relax" ) THEN
   CALL SYSTEM('cat $qvasppath/exefile/INCAR/INCAR-base > INCAR ')
   CALL SYSTEM('cat $qvasppath/exefile/INCAR/INCAR-relax >> INCAR ')
   WRITE(*,*)''
   WRITE(*,*)' The INCAR for structural optimization was generated sucessufully'
   WRITE(*,*)''
ELSE IF ( TRIM(ADJUSTL(key)) == "-elastic" ) THEN
   CALL SYSTEM('cat $qvasppath/exefile/INCAR/INCAR-base > INCAR ')
   CALL SYSTEM('cat $qvasppath/exefile/INCAR/INCAR-elastic >> INCAR ')
   WRITE(*,*)''
   WRITE(*,*)' The INCAR for elastic calculation was generated sucessufully'
   WRITE(*,*)''
ELSE IF ( TRIM(ADJUSTL(key)) == "-scf" ) THEN
   CALL SYSTEM('cat $qvasppath/exefile/INCAR/INCAR-base > INCAR ')
   CALL SYSTEM('cat $qvasppath/exefile/INCAR/INCAR-scf >> INCAR ')
   WRITE(*,*)''
   WRITE(*,*)' The INCAR for sef-consistent calculation was generated sucessufully'
   WRITE(*,*)''
ELSE IF ( TRIM(ADJUSTL(key)) == "-band" ) THEN
   CALL SYSTEM('cat $qvasppath/exefile/INCAR/INCAR-base > INCAR ')
   CALL SYSTEM('cat $qvasppath/exefile/INCAR/INCAR-band >> INCAR ')
   WRITE(*,*)''
   WRITE(*,*)' The INCAR for band structure calculation was generated sucessufully'
   WRITE(*,*)''
ELSE IF ( TRIM(ADJUSTL(key)) == "-dos" ) THEN
   CALL SYSTEM('cat $qvasppath/exefile/INCAR/INCAR-base > INCAR ')
   CALL SYSTEM('cat $qvasppath/exefile/INCAR/INCAR-dos >> INCAR ')
   WRITE(*,*)''
   WRITE(*,*)' The INCAR for density of state calculation was generated sucessufully'
   WRITE(*,*)''
ELSE IF ( TRIM(ADJUSTL(key)) == "-elf" ) THEN
   CALL SYSTEM('cat $qvasppath/exefile/INCAR/INCAR-base > INCAR ')
   CALL SYSTEM('cat $qvasppath/exefile/INCAR/INCAR-elf >> INCAR ')
   WRITE(*,*)''
   WRITE(*,*)' The INCAR for electron localization function was generated sucessufully'
   WRITE(*,*)''
ELSE IF ( TRIM(ADJUSTL(key)) == "-wk" ) THEN
   CALL SYSTEM('cat $qvasppath/exefile/INCAR/INCAR-base > INCAR ')
   CALL SYSTEM('cat $qvasppath/exefile/INCAR/INCAR-workfunction >> INCAR ')
   WRITE(*,*)''
   WRITE(*,*)' The INCAR for work function calculation was generated sucessufully'
   WRITE(*,*)''
ELSE IF ( TRIM(ADJUSTL(key)) == "-bader" ) THEN
   CALL SYSTEM('cat $qvasppath/exefile/INCAR/INCAR-base > INCAR ')
   CALL SYSTEM('cat $qvasppath/exefile/INCAR/INCAR-bader >> INCAR ')
   WRITE(*,*)''
   WRITE(*,*)' The INCAR for Bader charge was generated sucessufully'
   WRITE(*,*)''
ELSE IF ( TRIM(ADJUSTL(key)) == "-hse" ) THEN
   CALL SYSTEM('cat $qvasppath/exefile/INCAR/INCAR-base > INCAR ')
   CALL SYSTEM('cat $qvasppath/exefile/INCAR/INCAR-hse >> INCAR ')
   WRITE(*,*)''
   WRITE(*,*)' The INCAR for HSE06 calculation was generated sucessufully'
   WRITE(*,*)''
ELSE IF ( TRIM(ADJUSTL(key)) == "-md" ) THEN
   CALL SYSTEM('cat $qvasppath/exefile/INCAR/INCAR-base > INCAR ')
   CALL SYSTEM('cat $qvasppath/exefile/INCAR/INCAR-md >> INCAR ')
   WRITE(*,*)''
   WRITE(*,*)' The INCAR for molecule dynamic simulation was generated sucessufully'
   WRITE(*,*)''
ELSE IF ( TRIM(ADJUSTL(key)) == "-partchg" ) THEN
   CALL SYSTEM('cat $qvasppath/exefile/INCAR/INCAR-base > INCAR ')
   CALL SYSTEM('cat $qvasppath/exefile/INCAR/INCAR-particalchg >> INCAR ')
   WRITE(*,*)''
   WRITE(*,*)' The INCAR for partical charge was generated sucessufully'
   WRITE(*,*)''
ELSE IF ( TRIM(ADJUSTL(key)) == "-freq" ) THEN
   CALL SYSTEM('cat $qvasppath/exefile/INCAR/INCAR-base > INCAR ')
   CALL SYSTEM('cat $qvasppath/exefile/INCAR/INCAR-freq >> INCAR ')
   WRITE(*,*)''
   WRITE(*,*)' The INCAR for frequency calculaltion was generated sucessufully'
   WRITE(*,*)''
ELSE IF ( TRIM(ADJUSTL(key)) == "-optics" ) THEN
   CALL SYSTEM('cat $qvasppath/exefile/INCAR/INCAR-base > INCAR ')
   CALL SYSTEM('cat $qvasppath/exefile/INCAR/INCAR-optics >> INCAR ')
   WRITE(*,*)''
   WRITE(*,*)' The INCAR for optical property was generated sucessufully'
   WRITE(*,*)''
ELSE IF ( TRIM(ADJUSTL(key)) == "-ts" ) THEN
   CALL SYSTEM('cat $qvasppath/exefile/INCAR/INCAR-base > INCAR ')
   CALL SYSTEM('cat $qvasppath/exefile/INCAR/INCAR-ts >> INCAR ')
   WRITE(*,*)''
   WRITE(*,*)' The INCAR for transition state search was generated sucessufully'
   WRITE(*,*)''
ELSE IF ( TRIM(ADJUSTL(key)) == "-lobster" ) THEN
   CALL SYSTEM('cat $qvasppath/exefile/INCAR/INCAR-base > INCAR ')
   CALL SYSTEM('cat $qvasppath/exefile/INCAR/INCAR-lobster >> INCAR ')
   WRITE(*,*)''
   WRITE(*,*)' The INCAR for crystal orbital overlap population was generated sucessufully'
   WRITE(*,*)''
ELSE IF ( TRIM(ADJUSTL(key)) == "-phonon" ) THEN
   CALL SYSTEM('cat $qvasppath/exefile/INCAR/INCAR-base > INCAR ')
   CALL SYSTEM('cat $qvasppath/exefile/INCAR/INCAR-phononpy >> INCAR ')
   CALL SYSTEM('bash $qvasppath/exefile/Tools/phononpy.sh')
   WRITE(*,*)''
   WRITE(*,*)' The INCAR for phonon spectrum was generated sucessufully'
   WRITE(*,*)''
!########################## POSCAR #################################
ELSE IF  ( TRIM(ADJUSTL(key)) == "-fix" ) THEN
  CALL SYSTEM('$qvasppath/exefile/POSCAR/fix-pos.x '//TRIM(ADJUSTL(jobname)))
ELSE IF ( TRIM(ADJUSTL(key)) == "-it" ) THEN
  CALL SYSTEM('bash $qvasppath/exefile/POSCAR/ts.sh -t '//TRIM(ADJUSTL(jobname)))
ELSE IF ( TRIM(ADJUSTL(key)) == "-it2" ) THEN
  CALL SYSTEM('bash $qvasppath/exefile/POSCAR/ts.sh -t2 '//TRIM(ADJUSTL(jobname)))
ELSE IF ( TRIM(ADJUSTL(key)) == "-zc" ) THEN
  CALL SYSTEM('bash $qvasppath/exefile/POSCAR/zc.sh -zc')
ELSE IF ( TRIM(ADJUSTL(key)) == "-c2p" ) THEN
  CALL SYSTEM('bash $qvasppath/exefile/POSCAR/cif2pos.sh '//TRIM(ADJUSTL(allkey)))
ELSE IF ( TRIM(ADJUSTL(key)) == "-c2p2" ) THEN
  CALL SYSTEM('bash $qvasppath/exefile/POSCAR/cif2pos2.sh '//TRIM(ADJUSTL(allkey)))
!########################## KPOINTS #################################
ELSE IF  ( TRIM(ADJUSTL(key)) == "-k" ) THEN
  CALL SYSTEM('$qvasppath/exefile/KPOINTS/kpoints.x '//TRIM(ADJUSTL(jobname)))
ELSE IF  ( TRIM(ADJUSTL(key)) == "-kline" ) THEN
  CALL SYSTEM('$qvasppath/exefile/KPOINTS/kpointsline '//TRIM(ADJUSTL(jobname)))
!########################## POTCAR #################################
ELSE IF ( TRIM(ADJUSTL(key)) == "-pw91" ) THEN
 CALL SYSTEM('bash $qvasppath/exefile/POTCAR/potcar.sh '//TRIM(ADJUSTL(allkey)))
ELSE IF ( TRIM(ADJUSTL(key)) == "-pbe" ) THEN
 CALL SYSTEM('bash $qvasppath/exefile/POTCAR/potcar.sh '//TRIM(ADJUSTL(allkey)))
ELSE IF ( TRIM(ADJUSTL(key)) == "-lda" ) THEN
 CALL SYSTEM('bash $qvasppath/exefile/POTCAR/potcar.sh '//TRIM(ADJUSTL(allkey)))
ELSE IF ( TRIM(ADJUSTL(key)) == "-cp" ) THEN
 CALL SYSTEM('bash $qvasppath/exefile/POTCAR/potcar.sh -cp')
!########################## Tools #################################
ELSE IF ( TRIM(ADJUSTL(key)) == "-e" ) THEN
 CALL SYSTEM('bash $qvasppath/exefile/Tools/energy.sh')
ELSE IF ( TRIM(ADJUSTL(key)) == "-mde" ) THEN
 CALL SYSTEM('bash $qvasppath/exefile/Tools/mde.sh')
ELSE IF ( TRIM(ADJUSTL(key)) == "-mdm" ) THEN
 CALL SYSTEM('bash $qvasppath/exefile/Tools/mdm.sh')
ELSE IF ( TRIM(ADJUSTL(key)) == "-bandd" ) THEN
 CALL SYSTEM('$qvasppath/exefile/Tools/band.x')
ELSE IF ( TRIM(ADJUSTL(key)) == "-phonond" ) THEN
 CALL SYSTEM('$qvasppath/exefile/Tools/phonond.sh')
ELSE IF ( TRIM(ADJUSTL(key)) == "-elasticd" ) THEN
 CALL SYSTEM('$qvasppath/exefile/Tools/elasticd.sh')
ELSE IF ( TRIM(ADJUSTL(key)) == "-dosd" ) THEN
 CALL SYSTEM('$qvasppath/exefile/Tools/dos.sh')
ELSE IF ( TRIM(ADJUSTL(key)) == "-wkd" ) THEN
 CALL SYSTEM('$qvasppath/exefile/Tools/wkd.sh')
ELSE IF ( TRIM(ADJUSTL(key)) == "-opticsd" ) THEN
 CALL SYSTEM('$qvasppath/exefile/Tools/optics.sh')
ELSE IF ( TRIM(ADJUSTL(key)) == "-ldos" ) THEN
 CALL SYSTEM('$qvasppath/exefile/Tools/ldos.sh '//TRIM(ADJUSTL(allkey))) 
ELSE IF ( TRIM(ADJUSTL(key)) == "-p2c" ) THEN
 CALL SYSTEM('$qvasppath/exefile/Tools/getcif.x '//TRIM(ADJUSTL(keywords)))
ELSE IF ( TRIM(ADJUSTL(key)) == "-sw" ) THEN
 CALL SYSTEM('$qvasppath/exefile/Tools/getcif.x '//TRIM(ADJUSTL(keywords)))
ELSE IF ( TRIM(ADJUSTL(key)) == "-orthcell" ) THEN
 CALL SYSTEM('bash $qvasppath/exefile/Tools/orthogonalize_cell.sh '//TRIM(ADJUSTL(keywords)))
ELSE IF ( TRIM(ADJUSTL(key)) == "-as" ) THEN
 CALL SYSTEM('$qvasppath/exefile/Tools/adsorptioncites.x '//TRIM(ADJUSTL(keywords)))
ELSE IF ( TRIM(ADJUSTL(key)) == "-clean" ) THEN
 CALL SYSTEM('bash $qvasppath/exefile/Tools/clean.sh')
ELSE IF ( TRIM(ADJUSTL(key)) == "-redlat" ) THEN
 CALL SYSTEM('bash $qvasppath/exefile/Tools/redlat')
ELSE IF ( TRIM(ADJUSTL(key)) == "-g" ) THEN
 CALL SYSTEM('bash $qvasppath/exefile/Tools/gauss.sh')
ELSE IF ( TRIM(ADJUSTL(key)) == "-zpe" ) THEN
 CALL SYSTEM('bash $qvasppath/exefile/Tools/zpe.sh -z')
ELSE IF ( TRIM(ADJUSTL(key)) == "-findsym" ) THEN
 CALL SYSTEM('$qvasppath/exefile/Tools/findsym '//TRIM(ADJUSTL(allkey)))
ELSE IF ( TRIM(ADJUSTL(key)) == "-sc" ) THEN
 CALL SYSTEM('$qvasppath/exefile/Tools/supercell '//TRIM(ADJUSTL(allkey))) ! supercell will read $2
ELSE IF ( TRIM(ADJUSTL(key)) == "-findcell" ) THEN
 CALL SYSTEM('$qvasppath/exefile/Tools/findcell '//TRIM(ADJUSTL(allkey)))
ELSE IF ( TRIM(ADJUSTL(key)) == "-gauss" ) THEN
 CALL SYSTEM('bash $qvasppath/exefile/Tools/gauss.sh')
ELSE IF ( TRIM(ADJUSTL(key)) == "-3dband" ) THEN
 CALL SYSTEM('$qvasppath/exefile/Tools/3d_band')
ELSE IF ( TRIM(ADJUSTL(key)) == "-hej" ) THEN
 CALL SYSTEM('$qvasppath/exefile/Tools/heterojunction '//TRIM(ADJUSTL(keywords)))
ELSE IF ( TRIM(ADJUSTL(key)) == "-mos" ) THEN
 CALL SYSTEM('$qvasppath/exefile/Tools/moires '//TRIM(ADJUSTL(keywords)))
ELSE IF ( TRIM(ADJUSTL(key)) == "-out2arc" ) THEN
 CALL SYSTEM('$qvasppath/exefile/Tools/out2arc')
ELSE IF ( TRIM(ADJUSTL(key)) == "-nanotube" ) THEN
 CALL SYSTEM('$qvasppath/exefile/Tools/nanotube '//TRIM(ADJUSTL(keywords)))
ELSE IF ( TRIM(ADJUSTL(key)) == "-cls" ) THEN
 CALL SYSTEM('$qvasppath/exefile/Tools/cleavesurface '//TRIM(ADJUSTL(keywords)))
ELSE IF ( TRIM(ADJUSTL(key)) == "-3dkpoints" ) THEN
 CALL SYSTEM('$qvasppath/exefile/Tools/3dkpoints')
ELSE IF ( TRIM(ADJUSTL(key)) == "-scissorb" ) THEN
 CALL SYSTEM('$qvasppath/exefile/Tools/scissor_band.x')
ELSE IF ( TRIM(ADJUSTL(key)) == "-scissord" ) THEN
 CALL SYSTEM('$qvasppath/exefile/Tools/scissor_dos')
ELSE IF ( TRIM(ADJUSTL(key)) == "-help" ) THEN               !!! for expand by user themselves
 CALL helpdoc()
ELSE IF ( TRIM(ADJUSTL(key)) == "-h" ) THEN               !!! for expand by user themselves
 CALL helpdoc()
ELSE IF ( TRIM(ADJUSTL(key)) == "--help" ) THEN               !!! for expand by user themselves
 CALL helpdoc()
ELSE 
 CALL SYSTEM('bash $qvasppath/exefile/Tools/USERTooLs/userdefine.sh '//TRIM(ADJUSTL(allkey)))
END IF

END PROGRAM main

SUBROUTINE helpdoc()
WRITE(*,'(A98)')'+================================================================================================+'
WRITE(*,'(A98)')'|                                       qvasp usage v2.25                                        |'
WRITE(*,'(A98)')'|                                                               Wencai,Yi                        |'
WRITE(*,'(A98)')'|                                                              2025.06.02                        |'
WRITE(*,'(A98)')'+=================== POSCAR =================== + =============== POTCAR ========================+'
WRITE(*,'(A98)')'| qvasp -fix  Fix atomic layer for POSCAR       | qvasp -pw91 ELE_Name  POTCAR from PAW_GGA_W91  |'
WRITE(*,'(A98)')'| qvasp -it   Insert points for TS cal.(method1)| qvasp -pbe ELE_Name   POTCAR from PAW_GGA_PBE  |'
WRITE(*,'(A98)')'| qvasp -it2  Insert points for TS cal.(method2)| qvasp -lda ELE_Name   POTCAR from PAW_LDA      |'
WRITE(*,'(A98)')'| qvasp -sc   Create supercell for POSCAR       | qvasp -cp             Check the POTCAR         |'
WRITE(*,'(A98)')'| qvasp -zc   Imaginary frequency correction    +================== KPOINTS =====================+'
WRITE(*,'(A98)')'| qvasp -c2p  Transfer cif file to POSCAR       | qvasp -k density   Create KPOINTS(Auto mesh)   |'
WRITE(*,'(A98)')'| qvasp -c2p2 Transfer cif file to POSCAR(MS)   | qvasp -kline       Create KPOINTS(Line mode)   |'
WRITE(*,'(A98)')'+=================== INCAR ==================== | qvasp -3k density  Create KPOINTS:3D materials |'
WRITE(*,'(A98)')'| qvasp -relax   For structure optimization cal.| qvasp -3dkpoints  Create KPOINTS for 3D band   |'
WRITE(*,'(A98)')'| qvasp -ts      For trasition state cal.       + ================== Tools ======================+|'
WRITE(*,'(A98)')'| qvasp -scf     For self_consistent cal.       | qvasp -e          Read energy from OUTCAR      |'
WRITE(*,'(A98)')'| qvasp -elf     For ELF cal.                   | qvasp -p2c        Transfer POSCAR to *.cif     |'
WRITE(*,'(A98)')'| qvasp -wk      For work fuction cal.          | qvasp -wkd        Obtain work function         |'
WRITE(*,'(A98)')'| qvasp -band    For energy band cal.           | qvasp -bandd      Obtain Bands data            |'
WRITE(*,'(A98)')'| qvasp -dos     For density of states cal.     | qvasp -dosd       Obtain DOS data              |'
WRITE(*,'(A98)')'| qvasp -bader   For Bader charge cal.          | qvasp -ldos 1 2   Obtain LDOS data             |'
WRITE(*,'(A98)')'| qvasp -hse     For HSE06 cal.                 | qvasp -mde        Obtain Energy data for MD    |'
WRITE(*,'(A98)')'| qvasp -md      For molecular dynamics cal.    | qvasp -mdm        Obtain Magnetic moment for MD|'
WRITE(*,'(A98)')'| qvasp -elastic For elastic constants cal.     | qvasp -elasticd   Obtain elastic constants     |'
WRITE(*,'(A98)')'| qvasp -partchg For partical charge cal.       | qvasp -findsym    Find the symmetry            |'
WRITE(*,'(A98)')'| qvasp -freq    For frequency cal.             | qvasp -zpe        Obtain ZPE value             |'
WRITE(*,'(A98)')'| qvasp -optics  For optics property cal.       | qvasp -opticsd    Get optics datas             |'
WRITE(*,'(A98)')'| qvasp -phonon  For phonon spectrum cal.       | qvasp -findcell   Find the pri-cell of CONTCAR |'
WRITE(*,'(A98)')'+======================================== Tools =================================================+'
WRITE(*,'(A98)')'| qvasp -nanotube POS1  Roll nanosheet          | qvasp -3dband     Obtain 3D band for 2D mater. |'
WRITE(*,'(A98)')'| qvasp -out2arc        Get trajectory file     | qvasp -cls POSCAR Cleaving surface             |'
WRITE(*,'(A98)')'| qvasp -gauss      Transfer OUTCAR to Gauss.log| qvasp -mos POSCAR Construct Moire superlattice |'
WRITE(*,'(A98)')'| qvasp -scissorb    Corrected band via scissor | qvasp -scissord   Corrected DOS via scissor    |'
WRITE(*,'(A98)')'| qvasp -sw POS1     Switch (a,b,c) axis of POS1| qvasp -orthcell   Construct orthogonalize_cell |'
WRITE(*,'(A98)')'| qvasp -as POS1     Analysis adsorption sites  | qvasp -redlat     Redefine lattice vectors:PDOS|'
WRITE(*,'(A98)')'| qvasp -hej POS1 POS2  Construct heterojunction| qvasp -clean      Clean output files           |'
CALL SYSTEM('cat $qvasppath/exefile/Tools/USERTooLs/help-ex')
WRITE(*,'(A98)')'+==================================== Devoloper Info ============================================+'
WRITE(*,'(A98)')'| If using qvasp in your research, please cite the paper: [1] W.Yi,G.Tang, et al.qvasp:A Flexible|'
WRITE(*,'(A98)')'| Toolkit for VASP Users in Materials Simulations, Comput. Phys. Commun., 2020, 257, 107535      |'
WRITE(*,'(A98)')'+================================================================================================+'
END SUBROUTINE helpdoc
