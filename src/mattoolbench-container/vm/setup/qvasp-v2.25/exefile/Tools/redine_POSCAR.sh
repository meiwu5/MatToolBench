#!/bin/sh

####### deal sorted_by_atomic_number.txt and sorted_by_custom_angle.txt #########
read -p "Which ID do you want to use in above table(eg 1 2):" trow

echo "Now we are starting to build a heterostructure"
#echo "Please customize the lattice parameters of the heterostructure:"
#echo "1) Lattice parameters of the lower material"
#echo "2) Lattice parameters of the upper material"
#echo "3) Average of the lattice parameters of the upper and lower materials"
#read -p "Please customize the lattice parameters of the heterostructure:" lattice_select
#while [ 1 -lt 3 ]
#do
# if [ $lattice_select == 1 -o $lattice_select == 2 -o $lattice_select == 3 ]; then
#   break;
# else
#  read -p "Invalid input, you should input a number between 1 and 3, reinput: " lattice_select
# fi
#done
read -p "Please customize the thickness of vacuum layer of the Moires strusture (unit: Angstrom):" vac_thickness
read -p "Please customize the layer spacing of the heterostructure (unit: Angstrom):" inter_spacing
#echo $lattice_select > heter.in
echo $vac_thickness >> heter.in
echo $inter_spacing >> heter.in   # heter.in is the input file for build-heter.x

echo " "
ttrow=`cat sorted_for_cus_chose.txt |wc -l`
for row in $trow
do
    if [ $row -gt $ttrow ]; then
     echo "Skipping $row, is beyond the line number of sorted_for_cus_chose.txt"
     continue 
    fi 
    x1=$(sed -n ${row}p sorted_for_cus_chose.txt | awk '{print $1}')
    y1=$(sed -n ${row}p sorted_for_cus_chose.txt | awk '{print $2}')
    x2=$(sed -n ${row}p sorted_for_cus_chose.txt | awk '{print $3}')
    y2=$(sed -n ${row}p sorted_for_cus_chose.txt | awk '{print $4}')
    z0=$(expr $x1 \* $y2 - $x2 \* $y1)
    if [ "$z0" -gt 0 ]
    then
        z1=1
    else
        z1=-1
    fi
    xx1=$(sed -n ${row}p sorted_for_cus_chose.txt | awk '{print $5}')
    yy1=$(sed -n ${row}p sorted_for_cus_chose.txt | awk '{print $6}')
    xx2=$(sed -n ${row}p sorted_for_cus_chose.txt | awk '{print $7}')
    yy2=$(sed -n ${row}p sorted_for_cus_chose.txt | awk '{print $8}')
    zz0=$(expr $xx1 \* $yy2 - $xx2 \* $yy1)
    if [ "$zz0" -gt 0 ]
    then
        z2=1
    else
        z2=-1
    fi
    cp POSCAR1 POSCAR
    (echo 400; echo $x1 $y1 0; echo $x2 $y2 0; echo 0 0 $z1) | $qvasppath/exefile/Tools/USERTooLs/vaspkit | grep 123
    mv SUPERCELL.vasp POSCAR
    mv TRANSMAT TRANSMAT-$row.1
    #echo 921 | $qvasppath/exefile/Tools/USERTooLs/vaspkit | grep 123  ## question
    $qvasppath/exefile/Tools/2d-center.x
    mv POSCAR_center POSCAR11
    cp POSCAR2 POSCAR
    (echo 400; echo $xx1 $yy1 0; echo $xx2 $yy2 0; echo 0 0 $z2) | $qvasppath/exefile/Tools/USERTooLs/vaspkit | grep 123
    mv SUPERCELL.vasp POSCAR
    mv TRANSMAT TRANSMAT-$row.2
    #echo 921 | $qvasppath/exefile/Tools/USERTooLs/vaspkit | grep 123   ### question
    $qvasppath/exefile/Tools/2d-center.x
    mv POSCAR_center POSCAR22
#fi    
$qvasppath/exefile/Tools/build-heter.x
mv heter.vasp moires-$row.vasp
echo "Successfully build heterostructure in moires-$row.vasp!"
done
#rm -f heter.in  # clean it
