import numpy as np
import scipy
from matplotlib.pylab import plot
import math
#import cmath
import scipy.integrate

#Operating and inlet conditions
Ya0 = 3000/1E6    #Initial CO mol fraction               #ppm             
Yae = 3000/1E6    #Entering CO mol fraction              #ppm
Yb0 = 0.0         #Initial CO2 mol fraction              #ppm
Ybe = 0.0         #Entering CO2 mol fraction             #ppm
Yc0 = 500/1E6     #Initial C3H8 mol fraction             #ppm
Yce = 500/1E6     #Entering C3H8 mol fraction            #ppm
Tk0 = 417         #Initial temperature                   #K
Tke = 417         #Entering temperature                  #K
R = 8.314         #Gas constant                          #m^3.Pa/(K.mol)
P = 101325        #Pressure                              #Pa
vmean = 2.4       #Linear mean fluid velocity            #m/s
Mflow = 0.64      #Average moar flowrate of fuel and air #mol/s

#Information of dimension and active sites
r0 = 5.45E-4      #Channel radius                                        #m
s0 = 20E-6        #Washcat thickness                                     #m
u0 = 90E-6        #Cordierite thickness                                  #m
dm = 0.106        #Diameter of monolith block                            #m
w_slice = 27.6316 #Weight of a monolith slice based on 630g per monolith #g
cpsi = 400        #Cells per square inch                      

#Details of porous media (Assume parallel pore)
re = 13.3E-9      #Equivalent pore radius   #m
por = 0.5         #Porosity                #m^3 gas/m^3
tau = 4           #Tortuosity                           

#Active sites per catalyst/washcoat
LPt = 2.0E-6      #Pt loading data from CO chemisorption on wc and cord  #mol(Pt)/g(cat)
aBET = 100        #BET surface from ASAP and autopore)                   #m2 (cat)/g(cat)
rho_wc = 1.3E6    #Loose buk density                                     #g/m3
rho_cord = 2.5E6  #Density of substrate                                  #g/m3
LPtc = 0.005468   #Data from weighing                                    #g(Pt)/g(cat)

#Common information of catalyst
zl = 0.005               #Channel length of 5mm thin slice                                #m
Avo = 6.022E23           #Avogadro number                                                 #mol^-1
MPt = 195.08             #Molar mass of Pt                                                #g(Pt)/mol(Pt)
a_m = 8.07E-20           #Surface area occupied by a Pt atom on a polycrystalline surface #m2
cpsm = cpsi/0.000645     #Cells / m^2
Amon = math.pi*(dm/2)**2 #Cross sectional area of monolith slice                          #m2
ncell = cpsm*Amon        #Number of cells
V_slice = Amon*zl        #Volume of a slice includeing voidage                            #m^3    
H = LPt/aBET             #Assume uniform active sites density                             #mol(Pt) m^-2(cat)
Av = aBET*rho_wc         #Internal Surface area per reactor vol                           #m2(cat) m^-3(cat)
r_gtc = por/(1-por)      #Ratio of voue of gas to solid                                   #m^3(gas) m ^-3(cat)
N_atom = LPtc*Avo/MPt    #No. of Pt atoms as deposited                                    
Ns_atom = LPt*Avo        #No. of Pt surface atoms
D = Ns_atom/N_atom       
Ssp = a_m*Avo*D/MPt
G = 1 /(Ssp*MPt)

#Parameter for calculating bulk diffusion coefficient
Mco = 28.01
Mair = 28.96
Mo2 = 32.0
Mco2 = 44.01
Mc3h8 = 44.1
Vco = 18.9
Vair = 20.1
Vco2 = 22.262
Vc3h8 = 65.34

#Grids
#axial direction
nz = 5
dz = zl/nz
z = np.zeros(nz)
z = np.linspace(dz,zl,nz)
dzs = dz**2

#radial direction solid
ns = 5
ds = s0/(ns-1)
s = np.linspace(0,s0,ns)
dss = ds**2

#radial direction cordierite
nu = 3
du = u0/nu
u = np.linspace(du,u0,nu)
dus = du**2

#Kinetic parameters for LHHW
pf=0.729e21
pg=965.5
pt=4.042e15
pv=2080.0
pw=3.98
act1=-12556.0
act2=961.0
act3=-1.08e4
act4=361.0
act5=11611.0

#Other parameters
YO2 = 0.0933
dHR = -282.55E3
DH = 1.09E-3
ff = 1.0

#Time parameters
tf = 1800
td = 1
t0 = 0
tout = np.arange(t0,tf+td,td)
nout = tf
n_steps = np.floor((tf-t0)/td)+1


#Set array to zeros
Ya = Yb = Yc = Tk = np.zeros(nz)
Yas = Ybs = Ycs = Tks = np.zeros((nz,ns))
Tku = np.zeros((nz,nu))

v = Dca = Dcb = Dcc = Dia = Dib = Dic = np.zeros(nz)
k_a = rho_a = Cp_a = Dt = Dit = miu = np.zeros(nz)
Rey = L = Gz = NuT = NuH = Nu = Sh = hm = kma = kmb = kmc = np.zeros(nz)

Dcas = Dcbs = Dccs = np.zeros((nz,ns))
Dkas = Dkbs = Dkcs = np.zeros((nz,ns))
Dvas = Dvbs = Dvcs = np.zeros((nz,ns))
Deas = Debs = Decs = np.zeros((nz,ns))

k_s = rho_s = Cp_s = Ds = np.zeros((nz,ns))
YCO = YCO2 = YHC = np.zeros((nz,ns))

k1 = k2 = k3 = k4 = k5 = Inh = np.zeros((nz,ns))
RCO = RHC = RCO2 = RTCO = RTHC = np.zeros((nz,ns))
dHR = dHRP = np.zeros((nz,ns))

k_u = rho_u = Cp_u = Du = np.zeros((nz,nu))
Tkuu = Tkuuu = np.zeros((nz,nu))
Tkuuu = np.zeros((nz,nu))
Tkuzz = np.zeros((nz,nu))
Tkee = np.zeros(nout+1)

Yazz = Ybzz = Yczz = Tkzz = np.zeros(nz)
Yaz = Ybz = Ycz = Tkz = np.zeros(nz)
Yass = Ybss = Ycss = Tkss = np.zeros((nz,ns))
Yasss = Ybsss = Ycsss = Tksss = np.zeros((nz,ns))
Yaszz = Ybszz = Ycszz = Tkszz = np.zeros((nz,ns))

            
#Initial condition
for i in range (0,nz):
    Ya[i] = Ya0
    Yb[i] = Yb0
    Yc[i] = Yc0
    Tk[i] = Tk0
    
    Y1 = np.insert(Ya, nz, Yb)
    Y2 = np.insert(Y1,len(Y1),Yc)
    Y3 = np.insert(Y2,len(Y2),Tk)
        
for jj in range (0,ns):
    for i in range(0,nz):
        Yas[i,jj] = Ya0
        Ybs[i,jj] = Yb0
        Ycs[i,jj] = Yc0
        Tks[i,jj] = Tk0
        
        Yas1 = Yas.ravel()
        Ybs1 = Ybs.ravel()
        Ycs1 = Ycs.ravel()
        Tks1 = Tks.ravel()

        Y4 = np.insert(Y3,len(Y3),Yas1)
        Y5 = np.insert(Y4,len(Y4),Ybs1)
        Y6 = np.insert(Y5,len(Y5),Ycs1)
        Y7 = np.insert(Y6,len(Y6),Tks1)
        
for jjj in range (0,nu):
    for i in range(0,nz):
            Tku[i,jjj] = Tk0            
            Tku1 = Tku.ravel()
            Y = np.insert(Y7,len(Y7),Tku1)


# Parameters in the gas phase
for i in range(0,nz):   
    v[i] = vmean*Tk[i]/298
    Dca[i] = (1.013E-2*Tk[i]**(1.75)*(1/Mco+1/Mair)**(0.5))/(P*(Vco**(0.3333)+Vair**(0.3333))**2)
    Dcb[i] = (1.013E-2*Tk[i]**1.75*(1/Mco2+1/Mair)**0.5)/(P*(Vco2**(0.3333)+Vair**(0.3333))**2)
    Dcc[i] = (1.013E-2*Tk[i]**1.75*(1/Mc3h8+1/Mair)**0.5)/(P*(Vc3h8**(0.3333)+Vair**(0.3333))**2)
    Dia[i] = Dca[i] + (v[i]*r0)**2.0/(48.0*Dca[i])
    Dib[i] = Dcb[i] +(v[i]*r0)**2/(48*Dcb[i])
    Dic[i] = Dcc[i] +(v[i]*r0)**2/(48*Dcc[i])

    k_a[i] = 1.679E-2+5.073E-5*Tk[i]
    rho_a[i] = P*Mair/(1000*R*Tk[i])
    Cp_a[i] = (28.09+1.965E-3*Tk[i]+4.799E-6*Tk[i]**2-1.965E-9*Tk[i]**3)/(Mair/1000)
    Dt[i] = k_a[i]/(rho_a[i]*Cp_a[i])
    Dit[i] = Dt[i]+(v[i]*r0)**2/(48*Dt[i])

    miu[i] =7.701E-6+4.166E-8*Tk[i]-7.531E-12*Tk[i]**2
    Rey[i] = rho_a[i]*vmean*DH/miu[i]
    Pr = 0.7
    L[i] = (i+1)*dz
    Gz[i] = Rey[i]*Pr*DH/L[i]
    NuT[i] = 3.657+8.827*(1000/Gz[i])**-0.545*math.exp(-48.2/Gz[i])
    NuH[i] = 4.367+13.18*(1000/Gz[i])**-0.524*math.exp(-60.2/Gz[i])
    Nu[i] = (NuT[i]+NuH[i])/2+2 # Combined Nusselt Number

    Sh[i] =Nu[i]
    kma[i] = Sh[i]*Dca[i]/DH
    kmb[i] = Sh[i]*Dcb[i]/DH
    kmc[i] = Sh[i]*Dcc[i]/DH
    hm[i] = Nu[i]*k_a[i]/DH


# Parameters in the solid phase
for jj in range (0,ns):
    for i in range(0,nz):
        YCO[i,jj] = Yas [i,jj]
        YCO2[i,jj] = Ybs[i,jj]
        YHC[i,jj] = Ycs[i,jj]
        
        Dcas[i,jj] = (1.013E-2*Tks[i,jj]**1.75*(1/Mco+1/Mair)**(0.5))/(P*(Vco**(0.3333)+Vair**(0.3333))**2)
        Dcbs[i,jj] = (1.013E-2*Tks[i,jj]**1.75*(1/Mco2+1/Mair)**0.5)/(P*(Vco2**(0.3333)+Vair**(0.3333))**2)
        Dccs[i,jj] = (1.013E-2*Tks[i,jj]**1.75*(1/Mc3h8+1/Mair)**0.5)/(P*(Vc3h8**(0.3333)+Vair**(0.3333))**2)
        Dkas[i,jj] = 97.0*re*(Tks[i,jj]/Mco)**0.5
        Dkbs[i,jj] = 97.0*re*(Tks[i,jj]/Mco2)**0.5
        Dkcs[i,jj] = 97.0*re*(Tks[i,jj]/Mc3h8)**0.5
        Dvas[i,jj] = 1/(1/Dcas[i,jj]+1/Dkas[i,jj])
        Dvbs[i,jj] = 1/(1/Dcbs[i,jj]+1/Dkbs[i,jj])
        Dvcs[i,jj] = 1/(1/Dccs[i,jj]+1/Dkcs[i,jj])
        Deas[i,jj] = ff*por*Dvas[i,jj]/tau
        Debs[i,jj] = ff*por*Dvbs[i,jj]/tau
        Decs[i,jj] = ff*por*Dvcs[i,jj]/tau

        k_s[i,jj] = 0.9558-2.09E-4*Tks[i,jj]
        rho_s[i,jj] = rho_wc/1000
        Cp_s[i,jj] = 948 + 0.2268*Tks[i,jj]
        Ds[i,jj] = k_s[i,jj]/(rho_s[i,jj]*Cp_s[i,jj])
        
        k1[i,jj] = pf*math.exp(act1/Tks[i,jj])
        k2[i,jj] = pg*math.exp(act2/Tks[i,jj])
        k3[i,jj]=pt*math.exp(act3/Tks[i,jj])
        k4[i,jj]=pv*math.exp(act4/Tks[i,jj])
        k5[i,jj]=pw*math.exp(act5/Tks[i,jj])
        Inh[i,jj]=Tks[i,jj]*(1+k2[i,jj]*YCO[i,jj]+k4[i,jj]*YHC[i,jj])**2*(1+k5[i,jj]*(YCO[i,jj])**2*(YHC[i,jj])**2)      
        RCO[i,jj]=k1[i,jj]*YCO[i,jj]*YO2/Inh[i,jj]*R*Tks[i,jj]/P   
        RHC[i,jj]=k3[i,jj]*YHC[i,jj]*YO2/Inh[i,jj]*R*Tks[i,jj]/P
        RCO2[i,jj]=RCO[i,jj]+RHC[i,jj]
        RTCO[i,jj]=k1[i,jj]*YCO[i,jj]*YO2/Inh[i,jj]
        RTHC[i,jj]=k3[i,jj]*YHC[i,jj]*YO2/Inh[i,jj]
        dHR = -282.55E3
        dHRP[i,jj]=-2.059E6+72.3*Tks[i,jj]-9.69E-2*Tks[i,jj]**2+4.34E-5*Tks[i,jj]**3+7.56e-9*Tks[i,jj]**4

#Integration
def pde(t,y):

    for i in range (0,nz):
        Ya[i] = y[i]
        Yb[i] = y[i+nz]
        Yc[i] = y[i+2*nz]
        Tk[i] = y[i+3*nz]

        for jj in range(0,ns):
            Yas[i,jj] = y[4*nz+i*ns+jj]
            Ybs[i,jj] = y[4*nz+i*ns+jj+ns*nz]
            Ycs[i,jj] = y[4*nz+i*ns+jj+2*ns*nz]
            Tks[i,jj] = y[4*nz+i*ns+jj+3*ns*nz]


    
    #Temperature profile
    rt1=200.0                # linear ramp time in second
    rt2=500.0                # linear ramp time in second
    rt3=300.0                # 300 s of constant temperature
    rt4=100.0                # linear ramp time in second
    rt5=200.0                # linear ramp time in second
    rt6=500.0                # linear ramp time in second
    Tkef1=505.0              # temperature point 1
    Tkef2=543.0              # temperature point 2, max
    Tkef4=485.0              # temperature point 3
    Tkef5=445.0              # temperature point 4
    mp1=(Tkef1-Tke)/rt1    # multiplier 1
    mp2=(Tkef2-Tkef1)/rt2  # multiplier 2
    # mp3 is flat therefore no equation
    mp4=(Tkef4-Tkef2)/rt4  # multiplier 4
    mp5=(Tkef5-Tkef4)/rt5  # multiplier 5
    mp6=(Tke-Tkef5)/rt6    # multiplier 6
    
    if f.t<rt1:             
        Tkee=Tke+mp1*f.t
        
    elif f.t<(rt1+rt2):      
        Tkee=Tkef1+mp2*(f.t-rt1)
        
    elif f.t<(rt1+rt2+rt3):       
        Tkee=Tkef2
        
    elif f.t<(rt1+rt2+rt3+rt4):                
        Tkee=Tkef2+mp4*(f.t-(rt1+rt2+rt3))
        
    elif f.t<(rt1+rt2+rt3+rt4+rt5):
        Tkee=Tkef4+mp5*(f.t-(rt1+rt2+rt3+rt4))
        
    elif f.t<(rt1+rt2+rt3+rt4+rt5+rt6):
        Tkee=Tkef5+mp6*(f.t-(rt1+rt2+rt3+rt4+rt5))
        
    else:
        Tkee=Tke
        
    # Gas phase        
    for i in range(0,nz):
        if (i ==0):
            Yazz[i] = (Ya[i+1]-2.0*Ya[i]+Yae)/dzs
            Ybzz[i] = (Yb[i+1]-2.0*Yb[i]+Ybe)/dzs
            Yczz[i] = (Yc[i+1]-2.0*Yc[i]+Yce)/dzs
            Tkzz[i] = (Tk[i+1]-2.0*Tk[i]+Tkee[f.t])/dzs

            Yaz[i]  = (Ya[i]-Yae)/dz
            Ybz[i]  = (Yb[i]-Ybe)/dz
            Ycz[i]  = (Yc[i]-Yce)/dz
            Tkz[i]  = (Tk[i]-Tkee[f.t])/dz

        elif (i<nz-1):

            Yazz[i] = (Ya[i+1]-2.0*Ya[i]+Ya[i-1])/dzs
            Ybzz[i] = (Yb[i+1]-2.0*Yb[i]+Yb[i-1])/dzs
            Yczz[i] = (Yc[i+1]-2.0*Yc[i]+Yc[i-1])/dzs
            Tkzz[i] = (Tk[i+1]-2.0*Tk[i]+Tk[i-1])/dzs

            Yaz[i]  = (Ya[i]-Ya[i-1])/dz
            Ybz[i]  = (Yb[i]-Yb[i-1])/dz
            Ycz[i]  = (Yc[i]-Yc[i-1])/dz
            Tkz[i]  = (Tk[i]-Tk[i-1])/dz


        else :
            Yazz[i] = 2*(Ya[i-1]-Ya[i])/dzs
            Ybzz[i] = 2*(Yb[i-1]-Yb[i])/dzs
            Yczz[i] = 2*(Yc[i-1]-Yc[i])/dzs
            Tkzz[i] = 2*(Tk[i-1]-Tk[i])/dzs

            Yaz[i]  = (Ya[i]-Ya[i-1])/dz
            Ybz[i]  = (Yb[i]-Yb[i-1])/dz
            Ycz[i]  = (Yc[i]-Yc[i-1])/dz
            Tkz[i]  = (Tk[i]-Tk[i-1])/dz

    
    for jj in range(0,ns):
        for i in range(0,nz):
            
            # Washcoat phase in radial direction
            if (jj == 0):   
                Yass[i,jj]= 1/por*(4.0*Deas[i,jj]*(Yas[i,jj+1]-Yas[i,jj])/dss+kma[i]*(Ya[i]-Yas[i,jj])/ds)
                Ybss[i,jj]= 1/por*(4.0*Debs[i,jj]*(Ybs[i,jj+1]-Ybs[i,jj])/dss+kmb[i]*(Yb[i]-Ybs[i,jj])/ds)
                Ycss[i,jj]= 1/por*(4.0*Decs[i,jj]*(Ycs[i,jj+1]-Ycs[i,jj])/dss+kmc[i]*(Yc[i]-Ycs[i,jj])/ds)
                Tkss[i,jj]= (4.0*Ds[i,jj])*(Tks[i,jj+1]-Tks[i,jj])/dss-hm[i]*(Tks[i,jj]-Tk[i])/(ds*rho_s[i,jj]*Cp_s[i,jj])

                
            elif (jj <ns-1):
                Yass[i,jj]=(1.0/(s[jj]))*(Yas[i,jj+1]-Yas[i,jj-1])/(2.0*ds)
                Ybss[i,jj]=(1.0/(s[jj]))*(Ybs[i,jj+1]-Ybs[i,jj-1])/(2.0*ds)
                Ycss[i,jj]=(1.0/(s[jj]))*(Ycs[i,jj+1]-Ycs[i,jj-1])/(2.0*ds)
                Tkss[i,jj]=(1.0/(s[jj]))*(Tks[i,jj+1]-Tks[i,jj-1])/(2.0*ds)

            else :
                Yass[i,jj]=0
                Ybss[i,jj]=0
                Ycss[i,jj]=0
                Tkss[i,jj]=0

            # Cordierite phase in radial direction
            if jj ==0 :
                Yasss[i,jj]=0
                Ybsss[i,jj]=0
                Ycsss[i,jj]=0
                Tksss[i,jj]=0

            elif (jj <ns-1):

                Yasss[i,jj] = (Yas[i,jj+1]-2*Yas[i,jj]+Yas[i,jj-1])/dss
                Ybsss[i,jj] = (Ybs[i,jj+1]-2*Ybs[i,jj]+Ybs[i,jj-1])/dss
                Ycsss[i,jj] = (Ycs[i,jj+1]-2*Ycs[i,jj]+Ycs[i,jj-1])/dss
                Tksss[i,jj] = (Tks[i,jj+1]-2*Tks[i,jj]+Tks[i,jj-1])/dss

            else:
                Yasss[i,jj] = 2*(Yas[i,jj-1]-Yas[i,jj])/dss
                Ybsss[i,jj] = 2*(Ybs[i,jj-1]-Ybs[i,jj])/dss
                Ycsss[i,jj] = 2*(Ycs[i,jj-1]-Ycs[i,jj])/dss
                Tksss[i,jj] = 2*(Tks[i,jj-1]-Tks[i,jj])/dss
                
            if (i ==0):
                Yaszz[i,jj] = 2*(Yas[i+1,jj]-Yas[i,jj])/dzs
                Ybszz[i,jj] = 2*(Ybs[i+1,jj]-Ybs[i,jj])/dzs
                Ycszz[i,jj] = 2*(Ycs[i+1,jj]-Ycs[i,jj])/dzs
                Tkszz[i,jj] = 2*(Tks[i+1,jj]-Tks[i,jj])/dzs

            elif (i<nz-1):
                Yaszz[i,jj] = (Yas[i+1,jj]-2.0*Yas[i,jj]+Yas[i-1,jj])/dzs
                Ybszz[i,jj] = (Ybs[i+1,jj]-2.0*Ybs[i,jj]+Ybs[i-1,jj])/dzs
                Ycszz[i,jj] = (Ycs[i+1,jj]-2.0*Ycs[i,jj]+Ycs[i-1,jj])/dzs
                Tkszz[i,jj] = (Tks[i+1,jj]-2.0*Tks[i,jj]+Tks[i-1,jj])/dzs

            else :
                Yaszz[i,jj] = 2*(Yas[i-1,jj]-Yas[i,jj])/dzs
                Ybszz[i,jj] = 2*(Ybs[i-1,jj]-Ybs[i,jj])/dzs
                Ycszz[i,jj] = 2*(Ycs[i-1,jj]-Ycs[i,jj])/dzs
                Tkszz[i,jj] = 2*(Tks[i-1,jj]-Tks[i,jj])/dzs
                                    
    Yat = np.zeros(nz)
    Ybt = np.zeros(nz)
    Yct = np.zeros(nz)
    Tkt = np.zeros(nz)
    Yast = np.zeros((nz,ns))
    Ybst = np.zeros((nz,ns))
    Ycst = np.zeros((nz,ns))
    Tkst = np.zeros((nz,ns))

    for i in range(0,nz):
        Yat[i] = (Dia[i]*Yazz[i] - v[i]*Yaz[i]-4.0*kma[i]*(Ya[i]-Yas[i,0])/DH)
        Ybt[i] = (Dib[i]*Ybzz[i] - v[i]*Ybz[i]-4.0*kmb[i]*(Yb[i]-Ybs[i,0])/DH)
        Yct[i] = (Dic[i]*Yczz[i] - v[i]*Ycz[i]-4.0*kmc[i]*(Yc[i]-Ycs[i,0])/DH)
        Tkt[i] = (Dit[i]*Tkzz[i] - v[i]*Tkz[i] +(4.0*hm[i]*(Tks[i,0]-Tk[i]))/(DH*Cp_a[i]*rho_a[i]))

    for jj in range(0,ns):
        for i in range(0,nz):
            if jj ==0:
                Yast[i,jj]= Yass[i,jj]+(1/por)*(Deas[i,jj]*(Yaszz[i,jj])-RCO[i,jj]*H*Av/r_gtc*R*Tks[i,jj]/P)
                Ybst[i,jj]= Ybss[i,jj]+(1/por)*(Debs[i,jj]*(Ybszz[i,jj])+RCO2[i,jj]*H*Av/r_gtc*R*Tks[i,jj]/P)
                Ycst[i,jj]= Ycss[i,jj]+(1/por)*(Decs[i,jj]*(Ycszz[i,jj])-RHC[i,jj]*H*Av/r_gtc*R*Tks[i,jj]/P)
                Tkst[i,jj]= Tkss[i,jj]+Ds[i,jj]*(Tkszz[i,jj])+(-RCO[i,jj]*dHR-RHC[i,jj]*dHRP[i,jj])*H*Av/(rho_s[i,jj]*Cp_s[i,jj])

                
            else:
                Yast[i,jj]= (1/por)*(Deas[i,jj]*(Yass[i,jj]+Yasss[i,jj]+Yaszz[i,jj])-RCO[i,jj]*H*Av/r_gtc*R*Tks[i,jj]/P)
                Ybst[i,jj]= (1/por)*(Debs[i,jj]*(Ybss[i,jj]+Ybsss[i,jj]+Ybszz[i,jj])+RCO2[i,jj]*H*Av/r_gtc*R*Tks[i,jj]/P)
                Ycst[i,jj]= (1/por)*(Decs[i,jj]*(Ycss[i,jj]+Ycsss[i,jj]+Ycszz[i,jj])-RHC[i,jj]*H*Av/r_gtc*R*Tks[i,jj]/P)
                Tkst[i,jj]= Ds[i,jj]*(Tkss[i,jj]+Tksss[i,jj]+Tkszz[i,jj])+(-RCO[i,jj]*dHR-RHC[i,jj]*dHRP[i,jj])*H*Av/(rho_s[i,jj]*Cp_s[i,jj])

    
    y1 = np.zeros(120)
    
    for i in range(0,nz):
        y1[i] = Yat[i]
        y1[i+nz] = Ybt[i]
        y1[i+2*nz] = Yct[i]
        y1[i+3*nz] = Tkt[i]

        for jj in range(0,ns):
            y1[4*nz+i*ns+jj] = Yast[i,jj]
            y1[4*nz+i*ns+jj+ns*nz] = Ybst[i,jj]
            y1[4*nz+i*ns+jj+2*ns*nz] = Ycst[i,jj]
            y1[4*nz+i*ns+jj+3*ns*nz] = Tkst[i,jj]
            
    return y1


#independent variable

f = scipy.integrate.ode(pde).set_integrator('vode',method = 'bdf', order =15,atol = 1E-5, rtol = 1E-5)
f.set_initial_value(Y7,0)
time = np.zeros(n_steps)
a = []
time = []
t =1
YYY =[]

Ya1 = np.zeros((n_steps,nz))
Yb1 = np.zeros((n_steps,nz))
Yc1 = np.zeros((n_steps,nz))
Tk1 = np.zeros((n_steps,nz))

Yas1 = np.zeros((n_steps,nz,ns))
Ybs1 = np.zeros((n_steps,nz,ns))
Ycs1 = np.zeros((n_steps,nz,ns))
Tks1 = np.zeros((n_steps,nz,ns))

Tku1 = np.zeros((n_steps,nz,nu))


for i in range(0,nz):
    Ya1[0,i] = Ya[i]
    Yb1[0,i] = Yb[i]
    Yc1[0,i] = Yc[i]
    Tk1[0,i] = Tk[i]

    for jj in range(0,ns):
        Yas1[0,i,jj] = Yas[i,jj]
        Ybs1[0,i,jj] = Ybs[i,jj]
        Ycs1[0,i,jj] = Ycs[i,jj]
        Tks1[0,i,jj] = Tks[i,jj]

while f.successful() and f.t < tf:
    f.integrate(f.t+td)
    time += [f.t]

    Y7 = f.y
    
    for i in range(0,nz):
        Ya[i] = f.y[i]
        Yb[i] = f.y[i+nz]
        Yc[i] = f.y[i+2*nz]
        Tk[i] = f.y[i+3*nz]

    for jj in range(0,ns):
        for i in range(0,nz):
            Yas[i,jj] = f.y[4*nz+i*ns+jj]
            Ybs[i,jj] = f.y[4*nz+i*ns+jj+ns*nz]
            Ycs[i,jj] = f.y[4*nz+i*ns+jj+2*ns*nz]
            Tks[i,jj] = f.y[4*nz+i*ns+jj+3*ns*nz]
        
    for i in range(0,nz):
        Ya1[t,i] = Ya[i]
        Yb1[t,i] = Yb[i]
        Yc1[t,i] = Yc[i]
        Tk1[t,i] = Tk[i]

    for jj in range(0,ns):
        for i in range(0,nz):
            Yas1[t,i,jj] = Yas[i,jj]
            Ybs1[t,i,jj] = Ybs[i,jj]
            Ycs1[t,i,jj] = Ycs[i,jj]
            Tks1[t,i,jj] = Tks[i,jj]
            
    Yazz = np.zeros(nz)
    Ybzz = np.zeros(nz)
    Yczz = np.zeros(nz)
    Tkzz = np.zeros(nz)

    Yaz = np.zeros(nz)
    Ybz = np.zeros(nz)
    Ycz = np.zeros(nz)
    Tkz = np.zeros(nz)

    Yass = np.zeros((nz,ns))
    Ybss = np.zeros((nz,ns))
    Ycss = np.zeros((nz,ns))
    Tkss = np.zeros((nz,ns))

    Yasss = np.zeros((nz,ns))
    Ybsss = np.zeros((nz,ns))
    Ycsss = np.zeros((nz,ns))
    Tksss = np.zeros((nz,ns))

    Yaszz = np.zeros((nz,ns))
    Ybszz = np.zeros((nz,ns))
    Ycszz = np.zeros((nz,ns))
    Tkszz = np.zeros((nz,ns))
    
    for i in range(0,nz):   
        v[i] = vmean*Tk[i]/298
        Dca[i] = (1.013E-2*Tk[i]**(1.75)*(1/Mco+1/Mair)**(0.5))/(P*(Vco**(0.3333)+Vair**(0.3333))**2)
        Dcb[i] = (1.013E-2*Tk[i]**1.75*(1/Mco2+1/Mair)**0.5)/(P*(Vco2**(0.3333)+Vair**(0.3333))**2)
        Dcc[i] = (1.013E-2*Tk[i]**1.75*(1/Mc3h8+1/Mair)**0.5)/(P*(Vc3h8**(0.3333)+Vair**(0.3333))**2)
        Dia[i] = Dca[i] + (v[i]*r0)**2.0/(48.0*Dca[i])
        Dib[i] = Dcb[i] +(v[i]*r0)**2/(48*Dcb[i])
        Dic[i] = Dcc[i] +(v[i]*r0)**2/(48*Dcc[i])

        k_a[i] = 1.679E-2+5.073E-5*Tk[i]
        rho_a[i] = P*Mair/(1000*R*Tk[i])
        Cp_a[i] = (28.09+1.965E-3*Tk[i]+4.799E-6*Tk[i]**2-1.965E-9*Tk[i]**3)/(Mair/1000)
        Dt[i] = k_a[i]/(rho_a[i]*Cp_a[i])
        Dit[i] = Dt[i]+(v[i]*r0)**2/(48*Dt[i])

        miu[i] =7.701E-6+4.166E-8*Tk[i]-7.531E-12*Tk[i]**2
        Rey[i] = rho_a[i]*vmean*DH/miu[i]
        Pr = 0.7
        L[i] = (i+1)*dz
        Gz[i] = Rey[i]*Pr*DH/L[i]
        NuT[i] = 3.657+8.827*(1000/Gz[i])**-0.545*math.exp(-48.2/Gz[i])
        NuH[i] = 4.367+13.18*(1000/Gz[i])**-0.524*math.exp(-60.2/Gz[i])
        Nu[i] = (NuT[i]+NuH[i])/2+2 #???

        Sh[i] =Nu[i]
        kma[i] = Sh[i]*Dca[i]/DH
        kmb[i] = Sh[i]*Dcb[i]/DH
        kmc[i] = Sh[i]*Dcc[i]/DH
        hm[i] = Nu[i]*k_a[i]/DH

            
    for jj in range (0,ns):
        for i in range(0,nz):
            YCO[i,jj] = Yas [i,jj]
            YCO2[i,jj] = Ybs[i,jj]
            YHC[i,jj] = Ycs[i,jj]
        
            Dcas[i,jj] = (1.013E-2*Tks[i,jj]**1.75*(1/Mco+1/Mair)**(0.5))/(P*(Vco**(0.3333)+Vair**(0.3333))**2)
            Dcbs[i,jj] = (1.013E-2*Tks[i,jj]**1.75*(1/Mco2+1/Mair)**0.5)/(P*(Vco2**(0.3333)+Vair**(0.3333))**2)
            Dccs[i,jj] = (1.013E-2*Tks[i,jj]**1.75*(1/Mc3h8+1/Mair)**0.5)/(P*(Vc3h8**(0.3333)+Vair**(0.3333))**2)
            Dkas[i,jj] = 97.0*re*(Tks[i,jj]/Mco)**0.5
            Dkbs[i,jj] = 97.0*re*(Tks[i,jj]/Mco2)**0.5
            Dkcs[i,jj] = 97.0*re*(Tks[i,jj]/Mc3h8)**0.5
            Dvas[i,jj] = 1/(1/Dcas[i,jj]+1/Dkas[i,jj])
            Dvbs[i,jj] = 1/(1/Dcbs[i,jj]+1/Dkbs[i,jj])
            Dvcs[i,jj] = 1/(1/Dccs[i,jj]+1/Dkcs[i,jj])
            Deas[i,jj] = ff*por*Dvas[i,jj]/tau
            Debs[i,jj] = ff*por*Dvbs[i,jj]/tau
            Decs[i,jj] = ff*por*Dvcs[i,jj]/tau

            k_s[i,jj] = 0.9558-2.09E-4*Tks[i,jj]
            rho_s[i,jj] = rho_wc/1000
            Cp_s[i,jj] = 948 + 0.2268*Tks[i,jj]
            Ds[i,jj] = k_s[i,jj]/(rho_s[i,jj]*Cp_s[i,jj])
        
            k1[i,jj] = pf*math.exp(act1/Tks[i,jj])
            k2[i,jj] = pg*math.exp(act2/Tks[i,jj])
            k3[i,jj]=pt*math.exp(act3/Tks[i,jj])
            k4[i,jj]=pv*math.exp(act4/Tks[i,jj])
            k5[i,jj]=pw*math.exp(act5/Tks[i,jj])
            Inh[i,jj]=Tks[i,jj]*(1+k2[i,jj]*YCO[i,jj]+k4[i,jj]*YHC[i,jj])**2*(1+k5[i,jj]*(YCO[i,jj])**2*(YHC[i,jj])**2)      
            RCO[i,jj]=k1[i,jj]*YCO[i,jj]*YO2/Inh[i,jj]*R*Tks[i,jj]/P   
            RHC[i,jj]=k3[i,jj]*YHC[i,jj]*YO2/Inh[i,jj]*R*Tks[i,jj]/P
            RCO2[i,jj]=RCO[i,jj]+RHC[i,jj]
            RTCO[i,jj]=k1[i,jj]*YCO[i,jj]*YO2/Inh[i,jj]
            RTHC[i,jj]=k3[i,jj]*YHC[i,jj]*YO2/Inh[i,jj]
            dHR = -282.55E3
            dHRP[i,jj]=-2.059E6+72.3*Tks[i,jj]-9.69E-2*Tks[i,jj]**2+4.34E-5*Tks[i,jj]**3+7.56e-9*Tks[i,jj]**4


    print f.t
    t+= 1
    f.set_initial_value(Y7,f.t)

rCO = np.zeros(nout)
r2CO = np.zeros(nout)
COconv = np.zeros(nout)
rHC = np.zeros(nout)
r2HC = np.zeros(nout)
HCconv = np.zeros(nout)
Tkee = np.zeros(nout)
    
for t in range (0,nout):
    rCO[t]=Mflow*(Yae-Ya1[t,nz-1]);              # CO Reaction rate in mol/s
    r2CO[t]=rCO[t]/V_slice;                     # CO Reaction rate per slice
    COconv[t]=(Yae-Ya1[t,nz-1])/Yae;             #CO conversion
    rHC[t]=Mflow*(Yce-Yc1[t,nz-1]);              # HC Reaction rate in mol/s
    r2HC[t]=rHC[t]/V_slice;                     # HC Reaction rate per slice
    HCconv[t]=(Yce-Yc1[t,nz-1])/Yce;             # HC conversion
    


    
