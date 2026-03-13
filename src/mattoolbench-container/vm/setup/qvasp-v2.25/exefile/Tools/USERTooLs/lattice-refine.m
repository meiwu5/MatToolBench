latt=[   3.3782863617         0.0000000000         0.0000000000
-1.6891435704         2.9256815856         0.0000000000
 0.0000000000         0.0000000000         6.9528589249];
o=[0 0 0 ]; 
z=[0.333333333  0.666666667  0.28301]; 
x=[-0.3333333333  0.333333333 -0.28301];                     

z=z-o;                                                                                                                     
x=x-o;                                                                                                                   
z=z*latt;                                                                                                                  
x=x*latt;                                                                                                                  
z=z/norm(z);                                                                                                               
x=x/norm(x);                                                                                                               
y=cross(z,x);                                                                                                              
y=y/norm(y);            
x=cross(y,z);           
tran=[x;y;z];                                                                                                              
format long;                                                                                                               
new_latt=latt*inv(tran)                                                                                                   
format short;

% Running method: matlab -nodesktop -nosplash -r lattice-refine
