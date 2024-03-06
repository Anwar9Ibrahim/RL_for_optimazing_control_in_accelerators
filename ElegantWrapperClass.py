#import libraries
import numpy as np
import pandas as pd
import holoviews as hv
import os, glob
from IPython.display import Latex
from IPython.display import Image

from io import StringIO
from bokeh.models import HoverTool
import os


hv.extension("bokeh")

"""%opts Curve Spread [width=700 height=300 show_grid=True \
            default_tools=['box_zoom','pan','wheel_zoom','reset']]
"""

class elegantWrapper:
    def __init__(self):
        """
        Initialize the Elegent wrapper.
        """
        self.s0=0
        self.w = "results/w.sdds"
        self.png = "results/image.png"
        #Inputs
        self.trackFilePath= "track.ele"
        self.machineFilePath= "machine.lte"
        self.s=0
        self.df_final = pd.DataFrame()

        #create the results file
        if not os.path.exists("results/"): os.mkdir("results/")
        # clear the "results" folder:
        for f in glob.glob('results/*'): os.remove(f)

    #to add some lines to the input file this is will help us get the output
    def process_w(self, input_w, output_w="results/w.sdds", z0=0):
        !sddsprocess $input_w $output_w \
            "-define=col,x_mm,x 1e3 *,symbol=x,units=mm" \
            "-define=col,y_mm,y 1e3 *,symbol=x,units=mm" \
            "-define=col,z_mm,t c_mks * -1 * $z0 + 1e3 *,symbol=z,units=mm" \
            "-define=col,xp_mrad,xp 1e3 *,symbol=x',units=mrad" \
            "-define=col,yp_mrad,yp 1e3 *,symbol=y',units=mrad" \
            "-define=col,E_GeV,p 0.511e-3 *,symbol=E,units=GeV"
    
    #print the input files to check our input this is a void function
    def printInputFiles(self):
        print("######### " +str(self.machineFilePath)+ " #########")
        with open(self.machineFilePath, "r") as file:
            print(file.read())
        print("######### " +str(self.trackFilePath)+ " #########")
        with open(self.trackFilePath, "r") as file:
            print(file.read())

    
    #update Input file is also a void function to change the values of the magnets and the structure of the accelerator line
    def updateInputFile(self, variables):
        #here we are only changing the values of the magnets
        content= self.changeInetialContent(variables)
        with open(self.machineFilePath, "w") as file:
            file.write(content)
            #print(file.write(content))
        
    #run simulation outputs a dataframe this is for the RL optimization code
    def runSimulation(self):        
        #!!! keep in mind that here we are passing the name of the input file statically
        !elegant track.ele
        self.observation= self.createObservation()
        return self.observation 

    #simulation for 1D scan is a void function    
    def simulateFor1Dscan(self):
        !elegant track.ele
    
    def process_toStream(self, input="results/w1.sdds"):
        self.s= !sdds2stream $input -par=s
        return float(self.s[0])
        
    #plots the particles positions on a vertical cut on the line 
    def visualizeXY(self):
        !sddsplot -lay=2,2 -device=lpng -output=$self.png "-title=" \
        -col=x_mm,y_mm -graph=dot,type=2 $self.w -endPanel \
        -col=yp_mrad,y_mm -graph=dot,type=2 $self.w -endPanel \
        -col=x_mm,xp_mrad -graph=dot,type=2  $self.w -endPanel \
        -col=yp_mrad,xp_mrad -graph=dot,type=2 $self.w
        return(self.png)

    
    #plots the energy of the particles a vertical cut on the line 
    def visualizeE(self):
        !sddsplot -device=lpng -output=$self.png -lay=2,2 "-title=" \
        -col=z_mm,E_GeV -graph=dot,type=2 $self.w -endPanel \
        -col=xp_mrad,E_GeV -graph=dot,type=2 $self.w -endPanel \
        -col=z_mm,x_mm -graph=dot,type=2 $self.w -endPanel \
        -col=xp_mrad,x_mm -graph=dot,type=2 $self.w
        return(self.png)

    #PostProcessing
    def analyzeBeamlineMagnets(self):
        out= !sdds2stream results/beamline.mag -col=ElementName,s,Profile -pipe=out

        DATA = StringIO("\n".join(out))
        df = pd.read_csv(DATA, names=['ElementName', 's', 'Profile'], delim_whitespace=True)
        return df
    
    #get and analyze the output file track.sig 
    def analyzeTrackSig(self):
        out = !sdds2stream results/track.sig -col=ElementName,s,minimum1,maximum1,minimum3,maximum3,Sx,Sy -pipe=out
        DATA = StringIO("\n".join(out))
        df = pd.read_csv(DATA, names=['ElementName','s','xmin','xmax','ymin','ymax','sigma_x','sigma_y'],
                        delim_whitespace=True)
        df['xmin'] = df['xmin']*1e3; df['xmax'] = df['xmax']*1e3 # mm
        df['ymin'] = df['ymin']*1e3; df['ymax'] = df['ymax']*1e3 # mm
        df['sigma_x'] = df['sigma_x']*1e3; df['sigma_y'] = df['sigma_y']*1e3 # mm
        self.dfTrackSig= df
        return self.dfTrackSig

    #get and analyze the output file track.cen
    def analyzeTrackCen(self):
        out = !sdds2stream results/track.cen -col=ElementName,s,Particles,pCentral,Cx,Cy,Charge -pipe=out
        DATA = StringIO("\n".join(out))
        self.df_cen = pd.read_csv(DATA, names=['ElementName','s','Particles','p','Cx','Cy','Charge'],
                        delim_whitespace=True)

        self.df_cen['p'] = 0.511*self.df_cen['p'] # MeV/c
        self.df_cen['Cx'] = 1e3*self.df_cen['Cx'] # mm
        self.df_cen['Cy'] = 1e3*self.df_cen['Cy'] # mm
        return self.df_cen

    #get and analyze the output file twiss.twi
    def analyzeTwissSddd(self):
        out = !sdds2stream results/twiss.twi \
            -col=ElementName,s,betax,betay,alphax,alphay,etax,etay,pCentral0,xAperture,yAperture -pipe=out
        DATA = StringIO("\n".join(out))
        self.df_twi = pd.read_csv(DATA, names=['ElementName','s','betax','betay','alphax','alphay',
                                    'etax','etay','p','xAperture','yAperture'],
                        delim_whitespace=True)
        self.df_twi['xAperture'] = 1e3* self.df_twi['xAperture'] # mm
        self.df_twi['yAperture'] = 1e3* self.df_twi['yAperture'] # mm
        return self.df_twi

    def closeFiles(self):
        folder_path = 'results/'
        for filename in os.listdir(folder_path):
            file_path = os.path.join(folder_path, filename)
            if os.path.isfile(file_path):
                try:
                    with open(file_path, 'a'):
                        pass
                    os.remove(file_path)
                except PermissionError:
                    # If the file is in use, try again after a short delay
                    time.sleep(1)
                    os.remove(file_path)
        
    def createObservation(self):

        df= self.analyzeBeamlineMagnets()
        self.dfTrackSig= self.analyzeTrackSig()
        self.df_cen= self.analyzeTrackCen()
        self.df_twi= self.analyzeTwissSddd()

        dfTrackSig_updated= self.dfTrackSig.drop('ElementName', axis=1)
        dfTrackSig_updated= dfTrackSig_updated.drop('s', axis=1)

        dfTrackCen_updated= self.df_cen.drop('ElementName', axis=1)
        dfTrackCen_updated= dfTrackCen_updated.drop('s', axis=1)

        self.df_final = pd.concat([self.df_final, self.df_twi], axis=1)
        self.df_final = pd.concat([self.df_final, dfTrackSig_updated], axis=1)
        self.df_final = pd.concat([self.df_final, dfTrackCen_updated], axis=1)

        self.df_final = self.df_final.loc[:, (self.df_final != self.df_final.iloc[0]).any()]

        #save the values in an excel file
        #self.df_final.to_csv('combined_sig_files.csv', index=False)

        # add the codes of the Element Names 
        tempList= self.df_final['ElementName']
        cat_data=pd.Categorical(tempList)
        self.df_final['ElementCodes']= cat_data.codes
        
        self.closeFiles()
        return self.df_final

    def getNumberOfDeliverdParticles(self):
        self.observation=self.createObservation()
        self.deliveredParticles= self.observation['Particles'][len(self.observation)-1]-self.observation['Particles'][0]
        return self.deliveredParticles 

    """#!!!! get the differce in reward between the last two rows 
    #!!!! this could be fixed to get the difference in reward between the bigining of the element and the end !!!!
    def getreward(self, i):
        if i>=1:
            self.reward= self.observation['Particles'][i]-self.observation['Particles'][i-1]
        else:
            self.reward= self.observation['Particles'][i]-self.observation['Particles'][i]
        """

    #get reward after a specific element end of each element
    def rewardEachElement(self, i):
        current_element= self.observation['ElementName'][i]
        for j in range(i, len(self.observation)):
            temp_element= self.observation['ElementName'][j]
            if temp_element != current_element:
                reward= self.observation['Particles'][j-1]-self.observation['Particles'][i]
                break
        return reward,j, current_element
        

    #we can say this is private function we call it only from inside of the updateInputfile
    def changeInetialContent(self, variables):
        content=f"""! Comments go after "!"

!q: charge,total=3.2e-9
q: charge,total=5.4e-10

w1: watch,filename="results/w1.sdds",mode=coord
w2: watch,filename="results/w2.sdds",mode=coord
w3: watch,filename="results/w3.sdds",mode=coord
w4: watch,filename="results/w4.sdds",mode=coord
w5: watch,filename="results/w5.sdds",mode=coord
w6: watch,filename="results/w6.sdds",mode=coord
w7: watch,filename="results/w7.sdds",mode=coord
w8: watch,filename="results/w8.sdds",mode=coord

MA:     MAXAMP, X_MAX=1.0e-2, Y_MAX=1.0e-2, ELLIPTICAL=1

!POSITRON INJECTION

Q1L0:  QUAD,L=0.18, K1={variables['Q1LOk1']}, HKICK={variables['Q1LOHKICK']}, VKICK={variables['Q1LOVKICK']}
Q1L1:  QUAD,L=0.18, K1={variables['Q1L1k1']}, HKICK={variables['Q1L1HKICK']}, VKICK={variables['Q1L1VKICK']}

Q1L10: QUAD,L=0.18, K1={variables['Q1L10k1']}, HKICK={variables['Q1L1OHKICK']}, VKICK={variables['Q1L1VKICK']}
Q1L2:  QUAD,L=0.18, K1={variables['Q1L2k1']}, HKICK={variables['Q1L2HKICK']}, VKICK={variables['Q1L2VKICK']}
Q1L3:  QUAD,L=0.18, K1={variables['Q1L3k1']}, HKICK={variables['Q1L3HKICK']}, VKICK={variables['Q1L3VKICK']}
Q1L4:  QUAD,L=0.18, K1={variables['Q1L4k1']}, HKICK={variables['Q1L4HKICK']}, VKICK={variables['Q1L4VKICK']}
Q1L7:  QUAD,L=0.18, K1={variables['Q1L7k1']}, HKICK={variables['Q1L7HKICK']}, VKICK={variables['Q1L7VKICK']}
Q1L8:  QUAD,L=0.18, K1={variables['Q1L8k1']}, HKICK={variables['Q1L8HKICK']}, VKICK={variables['Q1L8VKICK']}
Q1L9:  QUAD,L=0.18, K1={variables['Q1L9k1']}, HKICK={variables['Q1L9HKICK']}, VKICK={variables['Q1L9VKICK']}

BM1:    SBEND,  L=0.87808,      ANGLE=+0.785398, FSE={variables['BM1FSE']}
BM2:    SBEND,  L=0.87808,      ANGLE=+0.785398, FSE={variables['BM2FSE']}
BM3:    SBEND,  L=0.87808,      ANGLE=-0.785398, FSE={variables['BM3FSE']}
BM4:    SBEND,  L=0.87808,      ANGLE=-0.785398, FSE={variables['BM4FSE']}

LL0L1:  DRIFT,  L=0.12
LL1M1:  DRIFT,  L=0.14
LM1L2:  DRIFT,  L=0.305
LL2M2:  DRIFT,  L=0.305
LM2L3:  DRIFT,  L=0.225
LL3L4:  DRIFT,  L=0.815
LL4L5:  DRIFT,  L=0.815
LL5M3:  DRIFT,  L=0.225
LM3L6:  DRIFT,  L=0.305
LL6M4:  DRIFT,  L=0.305
LM4L7:  DRIFT,  L=0.24
LL7L8:  DRIFT,  L=0.14
LDB:    DRIFT,  L=0.3214
LL9L10: DRIFT,  L=0.14

DP0:    DRIFT,  L=1.9081

!LM01L0: DRIFT,  L=0.285
LM01L0: DRIFT,  L=1.0

!LL10M5: DRIFT,  L=0.24
LL10M5: DRIFT,  L=1.0
LM5M6:  DRIFT,  L=0.99574

!Apertures:
MMK: MAXAMP,	X_MAX = 0.012,	Y_MAX = 0.037
MBH: MAXAMP,	X_MAX = 0.035,	Y_MAX = 0.0123,	ELLIPTICAL=1
MBV: MAXAMP,	X_MAX = 0.0123,	Y_MAX = 0.035,	ELLIPTICAL=1
ML:  MAXAMP,	X_MAX = 0.025,	Y_MAX = 0.025,	ELLIPTICAL=1
MS1: MAXAMP,	X_MAX = 0.0125,	Y_MAX = 0.0125,	ELLIPTICAL=1

!Accelerating structure:
RFCavity_d: rfca,freq=2856e6,l=0.03498,volt=-4.46e5, phase=0, change_p0=1

Debuncher: line=(43*RFCavity_d)

MA2:    MAXAMP, X_MAX=10.0e-2, Y_MAX=10.0e-2, ELLIPTICAL=1

!PositronLine:

PInject: LINE=(LM01L0,Q1L0,LL0L1,Q1L1,LL1M1)
PTurn:  LINE=(MBH,BM1,ML,LM1L2,Q1L2,LL2M2,MBH,BM2,ML,LM2L3,Q1L3,LL3L4,w2,Q1L4,LL4L5,Q1L3,LL5M3,MBH,BM3,ML,LM3L6,Q1L2,LL6M4,MBH,BM4,ML)

Debuncher_line:        LINE=(LM4L7,Q1L7,LL7L8,Q1L4,LDB,MA,Debuncher,ML,LDB,Q1L9,LL9L10,Q1L10,LL10M5,MBV)

PositronLine:   LINE=(PInject,PTurn,Debuncher_line)

machine: LINE = (q,w1,MA2,PositronLine,w3)"""
        return content
    
       
