#!/bin/sh

$qvasppath/exefile/Tools/orthogonalize_cell.x
####### deal sorted_by_atomic_number.txt and sorted_by_custom_angle.txt #########
read -p "Which ID do you want to use in above table(eg 1 2):" trow

echo " "
ttrow=`cat sorted_by_atomic_number.dat |wc -l`
for row in $trow
do
    if [ $row -gt $ttrow ]; then
     echo "Skipping $row, is beyond the line number of sorted_for_cus_chose.txt"
     continue 
    fi 
    x1=$(sed -n ${row}p sorted_by_atomic_number.dat | awk '{print $2}')
    x2=$(sed -n ${row}p sorted_by_atomic_number.dat | awk '{print $3}')
    x3=$(sed -n ${row}p sorted_by_atomic_number.dat | awk '{print $4}')
    y1=$(sed -n ${row}p sorted_by_atomic_number.dat | awk '{print $5}')
    y2=$(sed -n ${row}p sorted_by_atomic_number.dat | awk '{print $6}')
    y3=$(sed -n ${row}p sorted_by_atomic_number.dat | awk '{print $7}')
    z1=$(sed -n ${row}p sorted_by_atomic_number.dat | awk '{print $8}')
    z2=$(sed -n ${row}p sorted_by_atomic_number.dat | awk '{print $9}')
    z3=$(sed -n ${row}p sorted_by_atomic_number.dat | awk '{print $10}')

    (echo 400; echo $x1 $x2 $x3; echo $y1 $y2 $y3; echo $z1 $z2 $z3) | $qvasppath/exefile/Tools/USERTooLs/vaspkit | grep 123
    sed -i '1s/^.*$/qvasp/' SUPERCELL.vasp
    mv SUPERCELL.vasp POSCAR-$row.vasp
    mv TRANSMAT TRANSMAT-$row
#fi    
echo "Successfully transfer to orthorhombic lattice in POSCAR-$row.vasp!"
done
#rm -f heter.in  # clean it
