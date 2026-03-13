#!/bin/bash

$qvasppath/exefile/Tools/wkd.x

cat > wk.plt <<!
set encoding iso_8859_1
set terminal  png truecolor enhanced font ", 60" size 1920, 1680
set style data linespoints
set size 0.8, 1
set origin 0.1, 0
unset ztics
unset key
set pointsize 1.8
#set linewidth 1.8

set xlabel "Distance point"
set ylabel "Energy (eV)"
set title "Workfunction"
set terminal  png truecolor enhanced font ", 60" size 1920, 1680
set output 'wk.png'
unset key

plot "vline.dat" with linespoints linecolor 3 linewidth 1.8
!
gnuplot wk.plt

rm wk.plt
