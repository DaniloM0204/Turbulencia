import numpy as np
import matplotlib.pyplot as plt 


#Compute therorical profiles
x=np.linspace(0.1,100000,1000000)
yp=x

#Laminar
up=yp
#Low-law
up1=(1.0/0.41)*np.log(yp)+5.0





#load cfl3d data at x=1.90334
data = np.loadtxt("CFL3D_X2.txt",skiprows=2)

#Antilogarithm of input data
al=10**data[:,0]

#Load openfoam data
#data1 = np.loadtxt("../postProcessing/sampleDict/20/profile0_U_wallShearStress.xy",skiprows=0)
#data2 = np.loadtxt("../postProcessing/sampleDict/20/profile1_U_wallShearStress.xy",skiprows=0)
data1 = np.loadtxt("../postProcessing/sampleDict/10/profile0.xy",skiprows=1)
data2 = np.loadtxt("../postProcessing/sampleDict/10/profile1.xy",skiprows=1)


#interpolate data
from scipy import interpolate
fint=interpolate.interp1d(data2[:,0],data2[:,4],kind='linear')

#interpolation function of each ws component
fintwsx=interpolate.interp1d(data2[:,0],data2[:,4],kind='linear')
fintwsy=interpolate.interp1d(data2[:,0],data2[:,5],kind='linear')
fintwsz=interpolate.interp1d(data2[:,0],data2[:,6],kind='linear')


#find value at a given point
#fint(xloc)

#Where to sample
xloc=1.90334   

#Input values
U = 1
nu = 2.0e-07
rho = 1.0

#Compute wall shear stress magnitude and velocity magnitude
#Shear stress units is in pascal must multiply by density in incompressible flows

ws = np.sqrt(data1[:,4]**2 + data1[:,5]**2 + data1[:,6]**2)
um = np.sqrt(data1[:,1]**2 + data1[:,2]**2 + data1[:,3]**2)

#wsm=0.0012264945506493506

#Only use intermpolated data of x component
#wsm=np.abs(fint(xloc))

#Use interpolated data of all component
wsm = np.sqrt(np.abs(fintwsx(xloc))**2+np.abs(fintwsy(xloc))**2+np.abs(fintwsz(xloc))**2)


utau=np.sqrt(wsm/rho)
ypn=utau*data1[:,0]/nu
upn=um/utau

#Plot profiles

plt.figure(figsize=(14, 8))

#Correlations
plt.plot(yp,up,label='Viscous sublayer')
plt.plot(yp,up1,label='log-law')

#cfl3d
#plt.plot(ypn,upn,'-o',ms=6)
plt.plot(al,data[:,1],'-',label='CFL3D')

#OpenFOAM
#plt.plot(ypn[0:],upn[0:],'-o',label='OpenFOAM')
plt.plot(ypn[1:],upn[1:],'-o', ms=5, label='OpenFOAM')

plt.xscale('log')
#plt.xlim(0.1,100000)
plt.ylim(0,40)

plt.grid()
plt.legend(loc=2)

plt.savefig("f1.png")



#Compute wall shear stress magnitude and velocity magnitude
#Shear stress units is in pascal must multiply by density in incompressible flows

ws2 = np.sqrt(data2[:,4]**2 + data2[:,5]**2 + data2[:,6]**2)

#Compute plate reaynolds X and friction coefficient

x_plate=np.linspace(0.00001,2,1000)
re_x=x_plate*U/nu
small=1e-12
#cf_re=0.0592/(re_x+1*small)**(0.2)
cf_re=0.0592/(re_x)**(0.2)

cf_of=ws2/(0.5*rho*U**2)
#cf_of=2*ws2

#Read data extracted from paraview

#mesh1 from blockMesh
data3 = np.loadtxt("./ws_m1.csv",skiprows=1,delimiter=',')
#mesh2 from NASA plot3d
data4 = np.loadtxt("./ws_m2.csv",skiprows=1,delimiter=',')

#Compute cf using paraview data

#ws_pv=np.sqrt(data3[:,1]**2.+data3[:,2]**2.+data3[:,3]**2.)
#l_pv=data3[:,9]
ws_pv=np.sqrt(data3[:,5]**2.+data3[:,6]**2.+data3[:,7]**2.)
l_pv=data3[:,11]
cf_pv=ws_pv/(0.5*rho*U**2.)

ws_pv1=np.sqrt(data4[:,5]**2.+data4[:,6]**2.+data4[:,7]**2.)
l_pv1=data4[:,12]
cf_pv1=ws_pv1/(0.5*rho*U**2.)

#read data from CFL3D and FUN3D
cf1 = np.loadtxt("./CFL3D.txt",skiprows=2)
cf2 = np.loadtxt("./FUN3D.txt",skiprows=2)

#Plot data

plt.figure(figsize=(14, 8))

plt.plot(data2[:,0],cf_of,'-',label='OpenFOAM')

#Mesh 1 takes WF
plt.plot(l_pv,cf_pv,label='Sampling using paraView - Mesh 1')

#Mesh 2 = NASA, resolves BL
plt.plot(l_pv1,cf_pv1,label='Sampling using paraView - Mesh 2')

plt.plot(cf1[:,0],cf1[:,1],'-',label='CFL3D')

plt.plot(cf2[:,0],cf2[:,1],'-',label='FUN3D')

plt.plot(x_plate,cf_re,label='correlation')

plt.xlabel('Plate length',fontsize=18)
plt.ylabel('Friction coefficient $c_f$',fontsize=18)

plt.xlim(0,2)
plt.ylim(0,0.015)
plt.grid()

plt.legend(loc=0)

plt.savefig("f2.png")

