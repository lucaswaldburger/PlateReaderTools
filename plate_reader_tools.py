#Plate Reader Tools

import numpy as np
import pandas as pd
import math

def readplate(filename,sheetname,skiprows,rows,columns,datalabels,cycles,horz):
    wholetc = pd.read_excel(filename,sheetname=sheetname,skiprows=skiprows)

    #Determine how the excel sheet is formatted: if horz == 1 then the cycle numbers run horizontally, otherwise if horz == 0 then the cycle numbers run vertically


    col_labels = []
    for i in range(rows):
        for j in range(columns):
            col_labels.append(chr(i + ord('A')) + str(j+1))

    #generate the empty array
    data = pd.DataFrame(columns = col_labels)

    #populate a panel with empty dataframes
    d = pd.Panel({datalabels[0]:data})
    for i in range(len(datalabels[1:])):
        d[datalabels[i+1]] = data

    cycleindex = 0
    dataindex = 0

    d[datalabels[dataindex]].set_value(cycleindex,col_labels,wholetc[col_labels].iloc[i])

    #Check for case #1
    if horz == 0:
        t = wholetc['Time [s]'].iloc[0:cycles].values/float(3600)

        for i in range(len(wholetc.iloc[:,0])):
            try:
                num = int(wholetc.iloc[i,0])
                if num < cycles:
                    d[datalabels[dataindex]].loc[cycleindex] = wholetc[col_labels].iloc[i]
                    cycleindex = cycleindex + 1
                elif num == cycles:
                    d[datalabels[dataindex]].loc[cycleindex] = wholetc[col_labels].iloc[i]
                    cycleindex = 0
                    dataindex = dataindex + 1
            except ValueError:
                continue

    #Check for case #2
    else:
        t = wholetc.iloc[0,1:cycles+1].values/float(3600)
        for i in range(len(wholetc.iloc[:,0])):
            if (wholetc.iloc[i,0] in col_labels and wholetc.iloc[i,0] != 'H12'):
                d[datalabels[dataindex]][col_labels[c]] = (wholetc.iloc[i,1:cycles+1])
                cycleindex = cycleindex + 1
            elif wholetc.iloc[i,0] == 'H12':
                d[datalabels[dataindex]][col_labels[c]] = (wholetc.iloc[i,1:cycles+1])
                cycleindex = 0
                dataindex = dataindex + 1
            else:
                continue
    return [d,t]

def computegrowthrate(OD,t):
    #Calculate the growth rate in doublings per hour

    #One step
    onestep = np.empty([len(t)-1,len(OD.columns)])
    for i in range(len(t)-1):
        ODdiff = (OD.iloc[i+1,:]-OD.iloc[i,:])/OD.iloc[i,:]
        tdiff = t[i+1]-t[i]
        onestep[i]=ODdiff/tdiff

    #Two step
    twostep = np.empty([len(t)-2,len(OD.columns)])
    for i in range(len(t)-2):
        ODdiff = (OD.iloc[i+2,:]-OD.iloc[i,:])/OD.iloc[i,:]
        tdiff = t[i+2]-t[i]
        twostep[i]=ODdiff/tdiff

    #Find the max growth rate for each well

    vals = np.isnan(twostep[0,:])
    flipvals = [not i for i in vals]
    twostep[0,flipvals]

    maxind=np.empty(len(twostep[0,:]))

    for i in range(len(twostep[0,:])):
        maxind[i]=np.argmax(twostep[:,i])

    maxgrowth = np.empty([8,12])

    for i in range(12):
        for j in range(8):
            maxgrowth[j,i] = np.max(twostep[:,i+j*12])

    maxOD = np.empty([8,12])

    for i in range(12):
        for j in range(8):
            maxOD[j,i] = np.max(OD.iloc[:,i+j*12])

    return [twostep, maxind, maxgrowth, maxOD]

def exponentialvalues(maxind,vals):
    plate = np.empty([8,12])
    for i in range(8):
        for j in range(12):
            plate[i,j] = np.nanmean([vals.iloc[int(maxind[i*12+j]-1),i*12+j],vals.iloc[int(maxind[i*12+j]),i*12+j],vals.iloc[int(maxind[i*12+j]+1),i*12+j]])
    return plate

def tptoplate(cycle,df):
    #takes a cycle number (or an array of cycle numbers) and generates a 96 well plate formatted array from the data
    cycle = cycle-1
    plate = np.empty([8,12])

    if type(cycle) == int:
        for i in range(8):
            for j in range(12):
                plate[i,j] = df.iloc[cycle,i*12+j]
    else:
        for i in range(8):
            for j in range(12):
                plate[i,j] = df.iloc[cycle[i*12+j],i*12+j]
    return plate
