/*  This little program can transform the *.cif file to   */
/*    the VASP input file POSCAR directly.                */
/*  Every one is welcomed to use this file for free.      */
/*  The author is newcomer in the field of programming,   */
/*    so bugs and naive in algorithm are unavoidable.     */
/*  Thanks for use!  Contact the author: phast@yahoo.cn   */
/*  Version: 0.6 Date: 2013.3.11                          */
/*  Known bugs: Fraction occupation is unsurported        */
/*    temporarily.                                        */

#include <stdio.h>
#include <math.h>
#include <string.h>
#include <stdlib.h>
#define PI 3.14159265
#define CUT 0.0001
	struct atom
	{
	int o;
	char ns[3];
	char nl[5];
	double x;
	double y;
	double z;
	};
main(argc,argv)
	int argc;
	char *argv[];
{
FILE *fp1,*fp2;
int i=0,j=0,jj=0,k=0,l=0,m=0,n=0,nel,natom[256],endf;
double a,b,c,alpha,beta,gamma;
char str_a[]="_cell_length_a";
char str_b[]="_cell_length_b";
char str_c[]="_cell_length_c";
char str_alpha[]="_cell_angle_alpha";
char str_beta[]="_cell_angle_beta";
char str_gamma[]="_cell_angle_gamma";
char str_site_stt[]="_atom_site_";
char str_site_sttn[]="_atom_site_label";
char str_site_sttx[]="_atom_site_fract_x";
char str_site_stty[]="_atom_site_fract_y";
char str_site_sttz[]="_atom_site_fract_z";
char str_eof[]="_eof";
char str_ope_st1[]="_symmetry_equiv_pos_as_xyz";
char str_ope_st2[]="_space_group_symop_operation_xyz";
char str_ope_sp[]="loop";
char str_ope_sp2[]="_cell_";
char fn1[]="_chemical_formula_sum";
char fn2[]="_chemical_name_mineral";
char fn3[]="_pd_phase_name";
char fn4[]="data_AMS_DATA_";
char crys_nam[64];
char elem[8];
int seq[4];
char elemx[32];
char elemy[32];
char elemz[32];
int ele[2];
double f,g,h;
struct atom a_s[1024];
struct atom a_s_sort[1024];
char atom_nam[256][3];

/*open input file*/
	if((fp1=fopen(argv[1],"r"))==NULL)
	{
	printf("\nNo input file!please use standard command \"qvasp -c2p name.cif\"!\n");
	printf("\n");
	exit(0);
	}

/*open or create output file*/
	if((fp2=fopen("POSCAR","wb"))==NULL)
	{
	printf("\n Can't create POSCAR file here!\n");
	printf("\n");
	exit(0);
	}

/*find the end of the input file*/
	endf=0;
	do
	{
	fseek(fp1,endf++,SEEK_SET);
	}while(fgetc(fp1)!=EOF);
	endf--;
/*find the end of the input file*/

/*initialization of the structure data*/
for(j=0;j<1024;j++)
{
a_s[j].o=0;
a_s[j].ns[0]=32;
a_s[j].ns[1]=32;
a_s[j].ns[2]=00;
a_s[j].nl[0]=32;
a_s[j].nl[1]=32;
a_s[j].nl[2]=32;
a_s[j].nl[3]=32;
a_s[j].nl[4]=00;
a_s[j].x=0.0000;
a_s[j].y=0.0000;
a_s[j].z=0.0000;

a_s_sort[j].o=0;
a_s_sort[j].ns[0]=32;
a_s_sort[j].ns[1]=32;
a_s_sort[j].ns[2]=00;
a_s_sort[j].nl[0]=32;
a_s_sort[j].nl[1]=32;
a_s_sort[j].nl[2]=32;
a_s_sort[j].nl[3]=32;
a_s_sort[j].nl[4]=00;
a_s_sort[j].x=0.0000;
a_s_sort[j].y=0.0000;
a_s_sort[j].z=0.0000;
}

/*initialization of the int array natom*/
for(j=0;j<256;j++)
{
natom[j]=0;
}

	fprintf(fp2,"Transfer by qvasp");
	fprintf(fp2,"\n    1.0\n");


/*find a,b,c,alpha,beta,gamma*/
	i=find(fp1,str_a,0);
	if(i==endf)
	printf("\nErorr! Format of the file is not correct 1!\n");
	fseek(fp1,i++,SEEK_SET);
	fscanf(fp1,"%lf",&a);
	i=find(fp1,str_b,0);
	if(i==endf)
	printf("\nErorr! Format of the file is not correct 2!\n");
	fseek(fp1,i++,SEEK_SET);
	fscanf(fp1,"%lf",&b);
	i=find(fp1,str_c,0);
	if(i==endf)
	printf("\nErorr! Format of the file is not correct 3!\n");
	fseek(fp1,i++,SEEK_SET);
	fscanf(fp1,"%lf",&c);
	i=find(fp1,str_alpha,0);
	if(i==endf)
	printf("\nErorr! Format of the file is not correct 4!\n");
	fseek(fp1,i++,SEEK_SET);
	fscanf(fp1,"%lf",&alpha);
	i=find(fp1,str_beta,0);
	if(i==endf)
	printf("\nErorr! Format of the file is not correct 5!\n");
	fseek(fp1,i++,SEEK_SET);
	fscanf(fp1,"%lf",&beta);
	i=find(fp1,str_gamma,0);
	if(i==endf)
	printf("\nErorr! Format of the file is not correct 6!\n");
	fseek(fp1,i++,SEEK_SET);
	fscanf(fp1,"%lf",&gamma);
/*end of find a,b,c,alpha,beta,gamma*/

	alpha=alpha*PI/180;
	beta=beta*PI/180;
	gamma=gamma*PI/180;
	fprintf(fp2,"    %lf    %lf    %lf    \n",a,0.0,0.0);
	fprintf(fp2,"    %lf    %lf    %lf    \n",b*(cos(gamma)),b*(sin(gamma)),0.0);
	fprintf(fp2,"    %lf",c*cos(beta));
	alpha=c*(cos(alpha)/cos(gamma)-cos(beta))*cos(gamma)/sin(gamma);
	gamma=sqrt(fabs(c*c*sin(beta)*sin(beta)-alpha*alpha));
	fprintf(fp2,"    %lf    %lf    \n",alpha,gamma);
	alpha=0;
	beta=0;
	gamma=0;

/*figure out the sequence of the atom site information*/
k=find(fp1,str_site_sttn,0);
if(k==endf)
	printf("\Erorr! Format of the file is not correct! 7\n"); 
for(j=i=0;i<=k;)
	{
	i=find(fp1,str_ope_sp,j);
	if(i>k)
		{
		k=i;
		i=j+1;
		jj=k;
		if(jj!=endf)
			jj=jj-5;
		break;
		}
	j=i;
	}
if(j==0)
	printf("\nErorr! Format of the file is not correct! 8\n");

seq[0]=find(fp1,str_site_sttn,i);
seq[1]=find(fp1,str_site_sttx,i);
seq[2]=find(fp1,str_site_stty,i);
seq[3]=find(fp1,str_site_sttz,i);
/*printf("seq_n=%d , seq_x=%d , seq_y=%d , seq_z=%d\n",seq[0],seq[1],seq[2],seq[3]);*/
for(k=0;k<4;k++)
{
j=seq[k];
seq[k]=0;
if(j==endf)
printf("\nErorr! Format of the file is not correct! 9\n");
for(l=i+2;l<j;l++)
	{
	fseek(fp1,l,SEEK_SET);
	if(fgetc(fp1)==10)
	seq[k]++;
	}
}
/*end of figure out the sequence of the atom site information*/
/*printf("seq_n=%d , seq_x=%d , seq_y=%d , seq_z=%d\n",seq[0],seq[1],seq[2],seq[3]);*/


/*find the real end*/
if(jj==endf)
{
	k=find(fp1,str_eof,i);
	if(k==endf)
		{
/*printf("no _eof found\n");*/
		for(k=i;k<endf-1;k++)
			{
			fseek(fp1,k,SEEK_SET);
			if(fgetc(fp1)==35)
				{
				k--;
				break;
				}
			}
		}
	else k=k-5;
	jj=k;
}
	for(;jj>i;jj--)
		{
		fseek(fp1,jj,SEEK_SET);
		if( ((ele[0]=fgetc(fp1))!=10)&&(ele[0]!=32)&&(ele[0]!=13) )
		break;
		}
/*printf("start=%d, stop=%d\n",i,jj);*/
/*end of find the real end*/

/*find the point of the starting of the atomic coordinates*/
for(l=0;l!=endf;i=l)
{
l=find(fp1,str_site_stt,i);
if(l>=jj)
break;
else i=l;
}
fseek(fp1,i,SEEK_SET);
ele[1]=fgetc(fp1);
while(ele[1]!=10)
{
fseek(fp1,i,SEEK_SET);
ele[1]=fgetc(fp1);
i++;
}
/*find the point of the starting of the atomic coordinates*/

/*input the coordinate of the atoms*/
	n=0;
	for(l=i;l<jj;)
	{
		fseek(fp1,i,SEEK_SET);
		ele[1]=fgetc(fp1);
		while((ele[1]==32)||(ele[1]==10)||(ele[1]==13))
		{
		fseek(fp1,++i,SEEK_SET);
		ele[1]=fgetc(fp1);
		}

		for(k=0;k<seq[0];k++)
		{
			do
			{
			fseek(fp1,i,SEEK_SET);
			ele[1]=fgetc(fp1);
			i++;
			}while(ele[1]==32);
			do
			{
			fseek(fp1,i,SEEK_SET);
			ele[1]=fgetc(fp1);
			i++;
			}while(ele[1]!=32);
		}
		fseek(fp1,i,SEEK_SET);
		ele[1]=fgetc(fp1);
		while((ele[1]==32)||(ele[1]==10)||(ele[1]==13))
		{
		fseek(fp1,++i,SEEK_SET);
		ele[1]=fgetc(fp1);
		}

	fseek(fp1,i,SEEK_SET);
	elem[0]=elem[1]=elem[2]=elem[3]=32;
	elem[4]=0;
	fscanf(fp1,"%c%c%c%c",&elem[0],&elem[1],&elem[2],&elem[3]);
		for(k=0,m=0;k<4;k++)
		{
		if(elem[k]==32)m=1;
		if(m==1)elem[k]=0;
		}
		if((elem[0]>122)||(elem[0]<65))
		break;
	for(k=0;k<4;k++)
	{
	a_s[n].nl[k]=elem[k];
	if((k<2)&&(elem[k]>60))
	a_s[n].ns[k]=elem[k];
	if(elem[k]==32)break;
	}
	i=l;
		for(k=0;k<seq[1];k++)
		{
			do
			{
			fseek(fp1,i,SEEK_SET);
			ele[1]=fgetc(fp1);
			i++;
			}while(ele[1]==32);
			do
			{
			fseek(fp1,i,SEEK_SET);
			ele[1]=fgetc(fp1);
			i++;
			}while(ele[1]!=32);
		}
	fseek(fp1,i,SEEK_SET);
	fscanf(fp1,"%lf",&f);

	i=l;
		for(k=0;k<seq[2];k++)
		{
			do
			{
			fseek(fp1,i,SEEK_SET);
			ele[1]=fgetc(fp1);
			i++;
			}while(ele[1]==32);
			do
			{
			fseek(fp1,i,SEEK_SET);
			ele[1]=fgetc(fp1);
                        /*printf("seq_n=%d \n",ele[1]);*/
			i++;
			}while(ele[1]!=32);
		}
	fseek(fp1,i,SEEK_SET);
	fscanf(fp1,"%lf",&g);

	i=l;
		for(k=0;k<seq[3];k++)
		{
			do
			{
			fseek(fp1,i,SEEK_SET);
			ele[1]=fgetc(fp1);
			i++;
			}while(ele[1]==32);
			do
			{
			fseek(fp1,i,SEEK_SET);
			ele[1]=fgetc(fp1);
			i++;
			}while(ele[1]!=32);
		}
	fseek(fp1,i,SEEK_SET);
	fscanf(fp1,"%lf",&h);


	f=1-(ceil(f)-f);
	if(fabs(1.0-f)<CUT)
	f=0.0;
	g=1-(ceil(g)-g);
	if(fabs(1.0-g)<CUT)
	g=0.0;
	h=1-(ceil(h)-h);
	if(fabs(1.0-h)<CUT)
	h=0.0;

	a_s[n].x=f;
	a_s[n].y=g;
	a_s[n].z=h;
	a_s[n].o=1;
	for(;i<jj;i++)
		{
		fseek(fp1,i,SEEK_SET);
		if(fgetc(fp1)==10)
		break;
		}
	l=++i;
	n++;
	}
/*end of input the coordinate of the atoms */

/*figure out starting and ending of the operators*/
i=find(fp1,str_ope_st1,0);
if(i==endf)
i=find(fp1,str_ope_st2,0);
j=find(fp1,str_ope_sp2,i);
if(j==endf)
j=find(fp1,str_ope_sp,i)-5;
else j=j-6;
/*end of figure out starting and ending of the operators*/

/*drill the operators, and do it*/
fseek(fp1,i,SEEK_SET);
m=1;
	do
	{
		fseek(fp1,++i,SEEK_SET);
		ele[0]=fgetc(fp1);
		while((ele[0]==10)||(ele[0]==32))
		{
		fseek(fp1,i,SEEK_SET);
		ele[0]=fgetc(fp1);
		++i;
		}

		for(l=i;l<=j;l++)
		{
		fseek(fp1,l,SEEK_SET);
		if((ele[0]=fgetc(fp1))==44)
		break;
		}
		k=0;
		i--;

	/*read x operation*/
		do
		{
		fseek(fp1,i+k,SEEK_SET);
		elemx[k]=fgetc(fp1);
		k++;
		}while(k<(l-i));
		for(;k<32;k++)
		elemx[k]=0;

		for(i=++l;l<=j;l++)
		{
		fseek(fp1,l,SEEK_SET);
		if((ele[0]=fgetc(fp1))==44)
		break;
		}
		k=0;

	/*read y operator*/
		do
		{
		fseek(fp1,i+k,SEEK_SET);
		elemy[k]=fgetc(fp1);
		k++;
		}while(k<(l-i));
		for(;k<32;k++)
		elemy[k]=0;

		i=l;
		fseek(fp1,i,SEEK_SET);
		ele[1]=fgetc(fp1);
		while((ele[1]==32)||(ele[1]==44))
		{
		fseek(fp1,++i,SEEK_SET);
		ele[1]=fgetc(fp1);
		}

		for(l=i;l<=j;l++)
		{
		fseek(fp1,l,SEEK_SET);
		if((ele[1]=fgetc(fp1)==32)||(ele[1]==10))
		break;
		}
		k=0;
		l--;

	/*read z operator*/
		do
		{
		fseek(fp1,i+k,SEEK_SET);
		elemz[k]=fgetc(fp1);
		k++;
		}while(k<(l-i));
		for(;k<32;k++)
		elemz[k]=0;

		i=l;
	/*end of drill the symmetry operator*/

	/*do the operations;*/
		for(k=0;k<n;k++)
		{
			a_s[k+m*n]=a_s[k];
			a_s[k+m*n].x=0.0;
			a_s[k+m*n].y=0.0;
			a_s[k+m*n].z=0.0;

	/*operate x coordinate*/
			for(l=0;l<32;l++)
			{
			if(elemx[l]==120)
				{
				if(elemx[l-1]==45)
				a_s[k+m*n].x=a_s[k+m*n].x+a_s[k].x*(-1);
				else
				a_s[k+m*n].x=a_s[k+m*n].x+a_s[k].x;
				}
			if(elemx[l]==121)
				{
				if(elemx[l-1]==45)
				a_s[k+m*n].x=a_s[k+m*n].x+a_s[k].y*(-1);
				else
				a_s[k+m*n].x=a_s[k+m*n].x+a_s[k].y;
				}
			if(elemx[l]==122)
				{
				if(elemx[l-1]==45)
				a_s[k+m*n].x=a_s[k+m*n].x+a_s[k].z*(-1);
				else
				a_s[k+m*n].x=a_s[k+m*n].x+a_s[k].z;
				}
			}

			for(l=0;l<32;l++)
			{
			if(elemx[l]==47)
				{
				if(elemx[l-2]==45)
				a_s[k+m*n].x=a_s[k+m*n].x-((double)(elemx[l-1]-48))/((double)(elemx[l+1]-48));
				else
				a_s[k+m*n].x=a_s[k+m*n].x+((double)(elemx[l-1]-48))/((double)(elemx[l+1]-48));
				break;
				}
			}
			a_s[k+m*n].x=1-(ceil(a_s[k+m*n].x)-a_s[k+m*n].x);
			if(fabs(1.0-a_s[k+m*n].x)<CUT)
			a_s[k+m*n].x=0.0;

	/*operate y coordinate*/
			for(l=0;l<32;l++)
			{
			if(elemy[l]==120)
				{
				if(elemy[l-1]==45)
				a_s[k+m*n].y=a_s[k+m*n].y+a_s[k].x*(-1);
				else
				a_s[k+m*n].y=a_s[k+m*n].y+a_s[k].x;
				}
			if(elemy[l]==121)
				{
				if(elemy[l-1]==45)
				a_s[k+m*n].y=a_s[k+m*n].y+a_s[k].y*(-1);
				else
				a_s[k+m*n].y=a_s[k+m*n].y+a_s[k].y;
				}
			if(elemy[l]==122)
				{
				if(elemy[l-1]==45)
				a_s[k+m*n].y=a_s[k+m*n].y+a_s[k].z*(-1);
				else
				a_s[k+m*n].y=a_s[k+m*n].y+a_s[k].z;
				}
			}

			for(l=0;l<32;l++)
			{
			if(elemy[l]==47)
				{
				if(elemy[l-2]==45)
				a_s[k+m*n].y=a_s[k+m*n].y-((double)(elemy[l-1]-48))/((double)(elemy[l+1]-48));
				else
				a_s[k+m*n].y=a_s[k+m*n].y+((double)(elemy[l-1]-48))/((double)(elemy[l+1]-48));
				break;
				}
			}
			a_s[k+m*n].y=1-(ceil(a_s[k+m*n].y)-a_s[k+m*n].y);
			if(fabs(1.0-a_s[k+m*n].y)<CUT)
			a_s[k+m*n].y=0.0;

	/*operate z coordinate*/
			for(l=0;l<32;l++)
			{
			if(elemz[l]==120)
				{
				if(elemz[l-1]==45)
				a_s[k+m*n].z=a_s[k+m*n].z+a_s[k].x*(-1);
				else
				a_s[k+m*n].z=a_s[k+m*n].z+a_s[k].x;
				}
			if(elemz[l]==121)
				{
				if(elemz[l-1]==45)
				a_s[k+m*n].z=a_s[k+m*n].z+a_s[k].y*(-1);
				else
				a_s[k+m*n].z=a_s[k+m*n].z+a_s[k].y;
				}
			if(elemz[l]==122)
				{
				if(elemz[l-1]==45)
				a_s[k+m*n].z=a_s[k+m*n].z+a_s[k].z*(-1);
				else
				a_s[k+m*n].z=a_s[k+m*n].z+a_s[k].z;
				}
			}

			for(l=0;l<32;l++)
			{
			if(elemz[l]==47)
				{
				if(elemz[l-2]==45)
				a_s[k+m*n].z=a_s[k+m*n].z-((double)(elemz[l-1]-48))/((double)(elemz[l+1]-48));
				else
				a_s[k+m*n].z=a_s[k+m*n].z+((double)(elemz[l-1]-48))/((double)(elemz[l+1]-48));
				break;
				}
			}
			a_s[k+m*n].z=1-(ceil(a_s[k+m*n].z)-a_s[k+m*n].z);
			if(fabs(1.0-a_s[k+m*n].z)<CUT)
			a_s[k+m*n].z=0.0;
		}
		m++;

	}
	while(i<j);
/*end of drill the operators, and do it*/

/*printf("m=%d, n=%d\n",m,n);*/
m=m*n;

/*figure out the number of the atoms*/
	for(k=0,nel=m;k<m;k++)
	{
	if(a_s[k].o==0)
	continue;
		for(l=k+1;l<m;l++)
		{
		if(a_s[l].o==0)
		continue;
		if((a_s[k].ns[1]==a_s[l].ns[1])&&(a_s[k].ns[0]==a_s[l].ns[0]))
			{
			nel--;
			a_s[l].o=0;
			}

		}
	}
/*end of figure out the number of the atoms*/

/*clear out the "order"*/
	for(k=0;k<m;k++)
	{
	a_s[k].o=1;
	}
/*end of clear out the "order"*/

/*reorgnize the atom:clear out the overfolded atoms*/
	for(l=0;l<m;l++)
	{
	if(a_s[l].o==0)
	continue;
		for(k=l+1;k<m;k++)
		{
		if(a_s[k].o==0)
		continue;
		if((fabs(a_s[k].x-a_s[l].x)<CUT)&&(fabs(a_s[k].y-a_s[l].y)<CUT)&&(fabs(a_s[k].z-a_s[l].z)<CUT))
			{
			a_s[k]=a_s[1023];
			}
		}
	}
/*end of reorgnize the atom:clear out the overfolded atoms*/


/*reorgnize the atoms:collect the same atoms*/
for(k=0,j=0;k<nel;k++)
{
a_s[1022]=a_s[j];
for(i=0;(a_s[i+j].ns[0]==a_s[1022].ns[0])&&(a_s[i+j].ns[1]==a_s[1022].ns[1]);i++);
natom[k]=i;
atom_nam[k][0]=a_s[j].ns[0];
atom_nam[k][1]=a_s[j].ns[1];
atom_nam[k][2]=0;
j=j+i;
}

i=0;
for(k=0;k<nel;k++)
{
 for(j=0;j<m;j++)
 {
  if((a_s[j].ns[1]==atom_nam[k][1])&&(a_s[j].ns[0]==atom_nam[k][0]))
  {a_s_sort[i]=a_s[j];
  i++;}
 }
}

for(j=0;j<m;j++)
a_s[j]=a_s_sort[j];

/*for(k=0;k<m;k++)
{
	for(l=k;l<m;l++)
	{
	if(a_s[1022].o==0)
		{
		if(a_s[l].o==0)
			{
			for(i=l+1;(i<m)&&(a_s[i].o==0);i++);
			a_s[1021]=a_s[l];
			a_s[l]=a_s[i];
			a_s[i]=a_s[1021];
                        printf("dududud i l ele %d %d %s \n",i,l,a_s[i].ns);
			}
		a_s[1022]=a_s[l];
		continue;
		}
	if((a_s[l].ns[0]!=a_s[1022].ns[0])||(a_s[l].ns[1]!=a_s[1022].ns[1]))
		{
		for(i=l;(i<m)&&((a_s[i].ns[0]!=a_s[1022].ns[0])||(a_s[i].ns[1]!=a_s[1022].ns[1]));i++);
			if(i>=m)
			break;
		a_s[1021]=a_s[l];
		a_s[l]=a_s[i];
		a_s[i]=a_s[1021];
                printf("hahhahaha i l %d %d %s \n",i,l,a_s[i].ns);
		}
	for(i=l+1;(i<m)&&((a_s[i].ns[0]!=a_s[1022].ns[0])||(a_s[i].ns[1]!=a_s[1022].ns[1]));i++);
	if(i>=m)
	break;
	}
	a_s[1022]=a_s[1023];
	k=l;
	for(i=l+1;(i<m)&&(a_s[i].o==0);i++);
	if(i>=m)
	break;
}*/
/*end of reorgnize the atoms:collect the same atoms*/

/*figure out the numbers of every atom*/
for(k=0,j=0;k<nel;k++)
{
a_s[1022]=a_s[j];
for(i=0;(a_s[i+j].ns[0]==a_s[1022].ns[0])&&(a_s[i+j].ns[1]==a_s[1022].ns[1]);i++);
natom[k]=i;
atom_nam[k][0]=a_s[j].ns[0];
atom_nam[k][1]=a_s[j].ns[1];
atom_nam[k][2]=0;
j=j+i;
}
/*end of figure out the numbers of every atom*/

/*for(k=1;k<=natom[255]+1;k++)*/
for(k=0;k<nel;k++)
fprintf(fp2,"  %s  ",atom_nam[k]);
fprintf(fp2,"\n"); 
for(k=0;k<nel;k++)
fprintf(fp2,"  %d  ",natom[k]);
/*fprintf(fp2,"           !  "); */
fprintf(fp2,"\n  Direct\n");
for(k=0;(k<m)&&(a_s[k].o!=0);k++)
{fprintf(fp2,"  %lf  %lf  %lf  \n",a_s[k].x,a_s[k].y,a_s[k].z); /*,a_s[k].ns);*/
}
fclose(fp1);
fclose(fp2);
}
/*end of function: main*/


/*find the string "str" in file "file" from the point "k" on*/
int find(FILE *file,char *str,int k)
{
int i,j;
char c,f,g;
fseek(file,k,SEEK_SET);
	for(i=k;(f=fgetc(file))!=EOF;)
	{
		for(j=0;j<strlen(str);j++)
		{
		fseek(file,i++,SEEK_SET);
		g=fgetc(file);
		if((g)!=str[j])
		break;
		}
		if(j>=strlen(str))
		break;
	}
return i;
}
/*end of function: find*/
