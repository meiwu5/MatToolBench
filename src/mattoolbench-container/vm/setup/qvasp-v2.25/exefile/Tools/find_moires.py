#!/usr/bin/env python3
import math
from numpy import *
import numpy as np
from  tkinter import _flatten

v = 6


def read_data(filename):
    basis_vector = zeros((3, 3)) 
    fp = open(filename, mode='r')
    fp.readline() 
    fractor = float(fp.readline()) 
    for i in range(3):
        basis_vector[i, :] = list(fp.readline().split())
        basis_vector[i, :] = list(map(float, basis_vector[i, :]))
    aa = fractor * dot(basis_vector[0, :], basis_vector[0, :]) ** 0.5
    bb = fractor * dot(basis_vector[1, :], basis_vector[1, :]) ** 0.5
    angle = math.acos(dot(basis_vector[0, 0:2], basis_vector[1, 0:2]) / ((dot(basis_vector[0, 0:2], basis_vector[0, 0:2]) ** 0.5) * (dot(basis_vector[1, 0:2], basis_vector[1, 0:2]) ** 0.5)))
    vector1 = array([math.cos(angle / 2) * aa, math.sin(angle / 2) * aa, 0])
    vector2 = array([math.cos(angle / 2) * bb, math.sin(angle / 2) * bb * (-1), 0])
    fp.readline()
    atom_num = list(fp.readline().split()) 
    atom_num = list(map(int, atom_num)) 
    num = 0
    for i in range(len(atom_num)):
        num += atom_num[i] 
    fp.close()
    return num, vector1, vector2


def save_data(l1, l2, dic, norm_veca, norm_vecb, norm_vecc, norm_vecd, it, filename,lattice_select):
    fp = open(filename, mode='w')
    qw = [0, 0, 0, 0, 0]
    int_width = 5 
    float_width = 15 
    num_decimals = 6   
    for i in it:
        m = dic['mm'][0][i]
        n = dic['nn'][0][i]
        if (l1[m, 0:5]==l2[n, 0:5]).all():  # repeat
          continue;
        if (l1[m, 0:5]*(-1)==l2[n, 0:5]).all():
          continue;
        #if l1[m, 6]>90.0001:            # make the angle to 90, added by Wencai Yi,not necessary
        #   l1[m, 6]=180.0-l1[m, 6]
        #if l2[n, 6]>90.0001:
        #   l2[n, 6]=180.0-l2[n, 6]
        ## add by Wencai Yi
        qw[0] = abs(l1[m, 6] - l2[n, 6])
        if lattice_select==1:  ## lower
         #qw[1] = 0.0 #abs(l1[m, 4] - l2[n, 4]) / l1[m, 4]
         qw[1] = abs(l1[m, 4] - l2[n, 4]) / l2[n, 4]
         #qw[3] = 0.0 #abs(l1[m, 5] - l2[n, 5]) / l1[m, 5]
         qw[2] = abs(l1[m, 5] - l2[n, 5]) / l2[n, 5]
        elif lattice_select==2:  ## upper
         qw[1] = abs(l1[m, 4] - l2[n, 4]) / l1[m, 4]
         #qw[2] = 0.0 #abs(l1[m, 4] - l2[n, 4]) / l2[n, 4]
         qw[2] = abs(l1[m, 5] - l2[n, 5]) / l1[m, 5]
         #qw[4] = 0.0 #abs(l1[m, 5] - l2[n, 5]) / l2[n, 5]
        elif lattice_select==3:  # both
         qw[1] = abs(l1[m, 4] - l2[n, 4]) / ((l1[m, 4]+l2[n, 4])/2.0)
         #qw[2] = abs(l1[m, 4] - l2[n, 4]) / l2[n, 4]
         qw[2] = abs(l1[m, 5] - l2[n, 5]) / ((l1[m, 5]+l2[n, 5])/2.0)
         #qw[4] = abs(l1[m, 5] - l2[n, 5]) / l2[n, 5]
        fp.write(str(int(l1[m, 0])).rjust(int_width, ' '))
        fp.write(str(int(l1[m, 1])).rjust(int_width, ' '))
        fp.write(str(int(l1[m, 2])).rjust(int_width, ' '))
        fp.write(str(int(l1[m, 3])).rjust(int_width, ' '))
        fp.write(str(int(l2[n, 0])).rjust(int_width, ' '))
        fp.write(str(int(l2[n, 1])).rjust(int_width, ' '))
        fp.write(str(int(l2[n, 2])).rjust(int_width, ' '))
        fp.write(str(int(l2[n, 3])).rjust(int_width, ' '))  ## vector 1-8
        fp.write(str(qw[0]).rjust(float_width + 10, ' '))   ## angle mismatch
        fp.write(str(np.around(l1[m, 6], 1)).rjust(float_width - 5, ' '))   # angle 1
        fp.write(str(np.round(l2[n, 6], 1)).rjust(float_width - 5, ' '))    # angle 2
        fp.write(str(np.around(qw[1], num_decimals)).rjust(float_width, ' ')) # lattice mis 1-4
        fp.write(str(np.round(qw[2], num_decimals)).rjust(float_width, ' '))
        #fp.write(str(np.around(qw[3], num_decimals)).rjust(float_width, ' '))
        #fp.write(str(np.around(qw[4], num_decimals)).rjust(float_width, ' '))
        fp.write(str(int(dic['N1_v'][0][i])).rjust(int_width + 5, ' '))   # 1 atomic number 
        fp.write(str(int(dic['N2_v'][0][i])).rjust(int_width, ' '))        # 2 atomic number
        fp.write(str(int(dic['N1_v'][0][i] + dic['N2_v'][0][i])).rjust(int_width, ' ')) # total atom number
        fp.write(str(round(dic['diff_angle'][0][i], num_decimals)).rjust(float_width, ' '))  ## goal angle mistmatch
        fp.write(str(round((norm_veca[m] + norm_vecc[n]) / 2, num_decimals)).rjust(float_width, ' '))  ## lattice length 1
        fp.write(str(round((norm_vecb[m] + norm_vecd[n]) / 2, num_decimals)).rjust(float_width, ' '))  ## lattice length 2
        fp.write("\n")
    fp.close()
    he = open("heter.in", mode='w')
    he.write(str(lattice_select))
    he.write("\n")
    he.close()

def sort_and_save_data(l1, l2, dic, norm_veca, norm_vecb, norm_vecc, norm_vecd,lattice_select):
    it = list(_flatten(sorted(enumerate(dic['N_v'][0]), key=lambda x: x[1])))  
    it = it[0::2] 
    filename = "sorted_by_atomic_number.txt"
    save_data(l1, l2, dic, norm_veca, norm_vecb, norm_vecc, norm_vecd, it, filename,lattice_select)
   # diff_angle = array(dic['diff_angle'][0])
   # array_it = array(it)
   # diff_angle = diff_angle[array_it]
   # temp_angle = sort(list(set(dic['diff_angle'][0]))) 
   # iit = []

   # for i in range(len(temp_angle)):
   #     logical = (diff_angle == temp_angle[i]) 
   #     array_it = list(array_it[logical]) 
   #     iit.append(array_it)
   #     array_it = array(it) 
   # it = _flatten(iit) 
   # filename = "sorted_by_custom_angle.txt"
   # save_data(l1, l2, dic, norm_veca, norm_vecb, norm_vecc, norm_vecd, it, filename,lattice_select) 


def get_l1_or_l2(a, b):
    Nv = (2 * v + 1)
    m12_n12 = array(list(range(v,-v-1,-1))).reshape((-1, 1))   # modified by Wencai Yi 
    #m12_n12 = array(list(range(-v, v+1))).reshape((-1, 1)) 
    
    l1_or_l2 = zeros((Nv ** 4, 7))
    l1_or_l2[:, 0] = repeat(m12_n12, Nv ** 3, axis=0).reshape((1, -1))  
    l1_or_l2[:, 1] = tile(repeat(m12_n12, Nv ** 2, axis=0), (Nv, 1)).reshape((1, -1))  
    l1_or_l2[:, 2] = tile(tile(repeat(m12_n12, Nv, axis=0), (Nv, 1)), (Nv, 1)).reshape((1, -1))  
    l1_or_l2[:, 3] = tile(m12_n12, (Nv ** 3, 1)).reshape((1, -1))  
    veca = tile(l1_or_l2[:, 0].reshape((-1, 1)), (1, 2)) * tile(a[0:2], (Nv ** 4, 1)) + tile(l1_or_l2[:, 1].reshape((-1, 1)), (1, 2)) * tile(b[0:2], (Nv ** 4, 1))
    vecb = tile(l1_or_l2[:, 2].reshape((-1, 1)), (1, 2)) * tile(a[0:2], (Nv ** 4, 1)) + tile(l1_or_l2[:, 3].reshape((-1, 1)), (1, 2)) * tile(b[0:2], (Nv ** 4, 1))
    norm_veca = (sum(veca ** 2, 1) ** 0.5).reshape((-1, 1))
    norm_vecb = (sum(vecb ** 2, 1) ** 0.5).reshape((-1, 1))
    logical = (norm_veca * norm_vecb != 0)  
    norm_veca = norm_veca[logical[:, 0]]
    norm_vecb = norm_vecb[logical[:, 0]]
    veca = veca[logical[:, 0], :]
    vecb = vecb[logical[:, 0], :]
    l1_or_l2 = l1_or_l2[logical[:, 0], :]
    dot_ab = sum(veca * vecb, 1).reshape((-1, 1))   
    cos_angle = dot_ab / (norm_veca * norm_vecb)
    logical = (abs(cos_angle) <= 1)  
    cos_angle = cos_angle[logical[:, 0]]
    norm_veca = norm_veca[logical[:, 0]]
    norm_vecb = norm_vecb[logical[:, 0]]
    l1_or_l2 = l1_or_l2[logical[:, 0], :]
    l1_or_l2[:, 4] = norm_veca.reshape((1, -1))
    l1_or_l2[:, 5] = norm_vecb.reshape((1, -1))
    l1_or_l2[:, 6] = (np.arccos(cos_angle) * 180 / math.pi).reshape((1, -1))
    return [l1_or_l2, _flatten(norm_veca.tolist()), _flatten(norm_vecb.tolist())]


def jibei(*varargin):
    [num1, a, b] = read_data(varargin[0])
    s1 = ((a[1] * b[2] - b[1] * a[2]) ** 2 + (b[0] * a[2] - a[0] * b[2]) ** 2 + (a[0] * b[1] - b[0] * a[1]) ** 2) ** 0.5
    [l1, norm_veca, norm_vecb] = get_l1_or_l2(a, b)
    [num2, c, d] = read_data(varargin[1])
    s2 = ((c[1] * d[2] - d[1] * c[2]) ** 2 + (d[0] * c[2] - c[0] * d[2]) ** 2 + (c[0] * d[1] - d[0] * c[1]) ** 2) ** 0.5
    [l2, norm_vecc, norm_vecd] = get_l1_or_l2(c, d)

    mis_ang = float(input("Please enter the maximum angle mismatch you are allowed (unit: degree): "))
    mis_rate = float(input("Please enter the maximum lattice mismatch rate you are allowed (generally 0.05): "))
   # ang_pre = float(input("Please enter the angle of the heterostructure you want (unit: degree): "))
    ang_pre = 0.0
    ### add by Wencai Yi
    #print("Please customize the lattice parameters of the heterostructure:")
    #print("1) Lattice parameters of the lower material")
    #print("2) Lattice parameters of the upper material")
    #print("3) Average of the lattice parameters of the upper and lower materials")
    #lattice_select=int(input("Please customize the lattice parameters of the heterostructure:"))
    lattice_select=3  # for moire superlattice
    print("Calculating, please wait a moment, it usually takes 30-50s.")
    dic = {'diff_angle': [], 'N1_v': [], 'N2_v': [], 'N_v': [], 'mm': [], 'nn': []}
    diff_angle = [] 
    N1_v = [] 
    N2_v = [] 
    N_v = [] 
    mm = [] 
    nn = [] 
    m = l1.shape[0] 
    n = l2.shape[0]
    l2_order = array(list(range(n))).reshape((-1, 1))
#qw1 qw2 qw3 qw4 is the lattice mismatch
    #print(lattice_select)
    for ip in range(m): 
        qw0 = (abs(repeat(l1[ip, 6], n, axis=0) - l2[:, 6]) < mis_ang)
        if lattice_select == 1: # lower material
         qw1 = 1 #(abs(repeat(l1[ip, 4], n, axis=0) - l2[:, 4]) / repeat(l1[ip, 4], n, axis=0) < mis_rate)
         qw2 = (abs(repeat(l1[ip, 4], n, axis=0) - l2[:, 4]) / l2[:, 4] < mis_rate)
         qw3 = 1 #(abs(repeat(l1[ip, 5], n, axis=0) - l2[:, 5]) / repeat(l1[ip, 5], n, axis=0) < mis_rate)
         qw4 = (abs(repeat(l1[ip, 5], n, axis=0) - l2[:, 5]) / l2[:, 5] < mis_rate)
        elif lattice_select == 2: # upper
         qw1 = (abs(repeat(l1[ip, 4], n, axis=0) - l2[:, 4]) / repeat(l1[ip, 4], n, axis=0) < mis_rate)
         qw2 = 1 #(abs(repeat(l1[ip, 4], n, axis=0) - l2[:, 4]) / l2[:, 4] < mis_rate)
         qw3 = (abs(repeat(l1[ip, 5], n, axis=0) - l2[:, 5]) / repeat(l1[ip, 5], n, axis=0) < mis_rate)
         qw4 = 1 #(abs(repeat(l1[ip, 5], n, axis=0) - l2[:, 5]) / l2[:, 5] < mis_rate)
        elif lattice_select == 3:
         qw1 = 1 #(abs(repeat(l1[ip, 4], n, axis=0) - l2[:, 4]) / repeat(l1[ip, 4], n, axis=0) < mis_rate)
         qw2 = (abs(repeat(l1[ip, 4], n, axis=0) - l2[:, 4]) / ((l2[:, 4]+ repeat(l1[ip, 4], n, axis=0))/2.0) < mis_rate)
         qw3 = 1 #(abs(repeat(l1[ip, 5], n, axis=0) - l2[:, 5]) / repeat(l1[ip, 5], n, axis=0) < mis_rate)
         qw4 = (abs(repeat(l1[ip, 5], n, axis=0) - l2[:, 5]) / ((l2[:, 5]+repeat(l1[ip, 5], n, axis=0))/2.0) < mis_rate)

        logical_1 = (qw0 * qw1 * qw2 * qw3 * qw4).astype(int)
        if sum(logical_1):  
            index1 = array(where(logical_1 == 1))  
            logical_2 = (abs(l2[index1[0], 0] - l2[index1[0], 2]) != 0) + (abs(l2[index1[0], 1] - l2[index1[0], 3]) != 0)  
            if l1[ip, 0] != l1[ip, 2] or l1[ip, 1] != l1[ip, 3] or sum(logical_2):
               if l1[ip, 0] != l1[ip, 2] or l1[ip, 1] != l1[ip, 3]:
                   index = index1[0].reshape((-1, 1))  
               elif l1[ip, 0] == l1[ip, 2] and l1[ip, 1] == l1[ip, 3]: 
                   logical_2 = logical_2.astype(int)
                   index2 = array(where(logical_2 == 1))
                   index = index1[0][index2[0]].reshape((-1, 1))  # the [0] in index1[0] was added by Wencai Yi
               aa = l1[ip, 0] * tile(a, (index.shape[0], 1)) + l1[ip, 1] * tile(b, (index.shape[0], 1))
               bb = l1[ip, 2] * tile(a, (index.shape[0], 1)) + l1[ip, 3] * tile(b, (index.shape[0], 1))
               cc = tile(l2[index, 0], (1, 3)) * tile(c, (index.shape[0], 1)) + tile(l2[index, 1], (1, 3)) * tile(d, (index.shape[0], 1))
               dd = tile(l2[index, 2], (1, 3)) * tile(c, (index.shape[0], 1)) + tile(l2[index, 3], (1, 3)) * tile(d, (index.shape[0], 1))
               temp_N1_v = (((aa[:, 1] * bb[:, 2] - bb[:, 1] * aa[:, 2]) ** 2 + (bb[:, 0] * aa[:, 2] - aa[:, 0] * bb[:, 2]) ** 2 + (
                       aa[:, 0] * bb[:, 1] - bb[:, 0] * aa[:, 1]) ** 2) ** 0.5 / s1 * num1).reshape((-1, 1))
               temp_N2_v = (((cc[:, 1] * dd[:, 2] - dd[:, 1] * cc[:, 2]) ** 2 + (dd[:, 0] * cc[:, 2] - cc[:, 0] * dd[:, 2]) ** 2 + (
                       cc[:, 0] * dd[:, 1] - dd[:, 0] * cc[:, 1]) ** 2) ** 0.5 / s2 * num2).reshape((-1, 1))
               N12_index = array(list(range(temp_N1_v.shape[0]))).reshape((-1, 1))
               logical = (np.around(temp_N1_v) != 0) * (np.around(temp_N2_v) != 0)  
               logical = logical.astype(int)
               ind = where(logical == 1)
               tem_l2_index = index[ind[0]]
               temp_N12_index = N12_index[ind[0]]
               logical = (abs(90 - l2[tem_l2_index, 6]) < 60).astype(int)
               if abs(90 - l1[ip, 6]) < 60 and sum(logical):
                   ind = where(logical == 1)
                   index = tem_l2_index[ind[0]]
                   N12_index = temp_N12_index[ind[0]]
                   diff_angle = diff_angle + (tile(round(abs(ang_pre - l1[ip, 6]), 1), (1, index.shape[0]))).tolist()  
                   N1_v = N1_v + (np.around(temp_N1_v[N12_index])).tolist()
                   N2_v = N2_v + (np.around(temp_N2_v[N12_index])).tolist()
                   N_v = N_v + ((temp_N1_v[N12_index] + temp_N2_v[N12_index]).reshape((1, -1))).tolist()
                   mm = mm + (tile(ip, (1, index.shape[0]))).tolist()
                   nn = nn + (index.reshape((1, -1))).tolist()
    dic['diff_angle'].append(list(_flatten(diff_angle)))
    dic['N1_v'].append(list(_flatten(N1_v)))
    dic['N2_v'].append(list(_flatten(N2_v)))
    dic['N_v'].append(list(_flatten(N_v)))
    dic['mm'].append(list(_flatten(mm)))
    dic['nn'].append(list(_flatten(nn)))
    sort_and_save_data(l1, l2, dic, norm_veca, norm_vecb, norm_vecc, norm_vecd,lattice_select)

jibei("POSCAR1", "POSCAR1")

#fp1 = open("sorted_by_atomic_number.txt", mode='r')
#atomic_number1 = fp1.readline().strip('\n').split()
#atomic_number2 = fp1.readline().strip('\n').split()
#atomic_number3 = fp1.readline().strip('\n').split()
#fp1.close()

#print("\n")
#print("*************************************************************")
#print("The calculation is complete! All results have been saved to ")
#print("sorted_by_atomic_number.txt and sorted_by_custom_angle.txt. ")
#print("Now, output the three matching schemes with the smallest number of atoms. ")
#print("1. atomic number: %s lattice constant(a): %s (b): %s angle: %s"  \
#      %(atomic_number1[17], atomic_number1[19], atomic_number1[20], atomic_number1[9]))
#print("2. atomic number: %s lattice constant(a): %s (b): %s angle: %s"  \
#      %(atomic_number2[17], atomic_number2[19], atomic_number2[20], atomic_number2[9]))
#print("3. atomic number: %s lattice constant(a): %s (b): %s angle: %s"  \
#      %(atomic_number3[17], atomic_number3[19], atomic_number3[20], atomic_number3[9]))
#print("Run redine_POSCAR.sh for the next step.")

