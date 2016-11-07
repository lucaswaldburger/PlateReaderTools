#Plate Reader Tools

import numpy as np
import pandas as pd
import math

def readplate(filename,sheetname,skiprows,rows,columns,datalabels,cycles):
    wholetc = pd.read_excel(filename,sheetname=sheetname,skiprows=skiprows)

    #Determine how the excel sheet is formatted:
    #1)The sheet can be formatted with cycle #s as the rows, or
    #2)With the well label as the rows
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

    c = 0
    ind = 0

    #Check for case #1
    if wholetc.iloc[3,0] == 4:
        t = wholetc['Time [s]'].iloc[0:cycles].values/float(3600)
        for i in range(len(wholetc.iloc[:,0])):
            if wholetc.iloc[i,0] < cycles:
                d[datalabels[ind]].set_value(c,col_labels,wholetc[col_labels].iloc[i])
                c = c + 1
            elif wholetc.iloc[i,0] == cycles:
                d[datalabels[ind]].set_value(c,col_labels,wholetc[col_labels].iloc[i])
                c = 0
                ind = ind + 1
            else:
                continue

    #Check for case #2
    else:
        t = wholetc.iloc[0,1:cycles+1].values/float(3600)
        for i in range(len(wholetc.iloc[:,0])):
            if (wholetc.iloc[i,0] in col_labels and wholetc.iloc[i,0] != 'H12'):
                d[datalabels[ind]][col_labels[c]] = (wholetc.iloc[i,1:cycles+1])
                c = c+1
            elif wholetc.iloc[i,0] == 'H12':
                d[datalabels[ind]][col_labels[c]] = (wholetc.iloc[i,1:cycles+1])
                c = 0
                ind = ind + 1
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

    return [twostep, maxind]

def exponentialvalues(maxind,vals):
    maxin = np.empty(96)
    for i in range(96):
        maxin[i]=np.mean([vals.iloc[int(maxind[i]-1),i],vals.iloc[int(maxind[i]),i],vals.iloc[int(maxind[i]+1),i]])

    return maxin

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
