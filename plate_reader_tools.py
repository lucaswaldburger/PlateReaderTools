#Plate Reader Tools

import numpy as np
import pandas as pd
import math
import string

def multiRead(filename, sheetname, delimiters):
    wells = []
    for i in range(8):
        for j in range(12):
            wells.append(chr(i + ord('A')) + str(j + 1))
            
    # get date from file name
    startDate = filename.find('20')
    endDate = filename[startDate:].find('_')
    date = filename[startDate:startDate + endDate]
    
    # determine if multiple reads per well
    rawData = pd.read_excel(filename, 'Result sheet', 0)
    infoColumn = rawData.iloc[:, 0]

    if 'Mean' in list(infoColumn) and len(infoColumn[infoColumn == 'Mean'].index) == len(delimiters):
        meanIndex = infoColumn[infoColumn == 'Mean'].index

        channels = [np.nan] * len(meanIndex)

        channelCount = 0
        for startRow in meanIndex:
            data = pd.read_excel(filename,'Result sheet',startRow)
            channels[channelCount] = pd.DataFrame(data.iloc[0:1,1:])
            channelCount += 1

        d = {}
        for i in range(len(delimiters)):
            d[delimiters[i]] = tptoplate(1,channels[i])
        data = pd.Panel(d)
        return data
    if 'Cycles / Well' in list(infoColumn):
        wellIndex = infoColumn[infoColumn == 'Cycles / Well'].index + 1
        raw_data = pd.read_excel(filename,sheetname,wellIndex[0])

        cycles = int(filter(str.isdigit, raw_data.columns[-1]))

        d = {}
        channels = []
        for i in range(len(delimiters)):
            raw_data = pd.read_excel(filename,sheetname,wellIndex[0 + 2 * 96])
            mean_index = []
            t = []
            t_index = 0
            read = []
            for i in range(len(raw_data.index)):
                if raw_data.loc[i,'Cycles / Well'] in delimiters:
                    break
                if raw_data.loc[i,'Cycles / Well'] in wells:
                    read.append(raw_data.loc[i,'Cycles / Well'])
                    mean_index.append(i+3)
                if raw_data.loc[i,'Cycles / Well'] == 'Time [s]' and len(t) == 0:
                    t_index = i
            mean_data = raw_data.iloc[mean_index,1:cycles+1]
            t = raw_data.iloc[t_index,1:cycles+1]
            mean_data.index = read
            mean_data.columns = range(1,cycles+1)
            channels.append(mean_data.T)
        for i in range(len(delimiters)):
            d[delimiters[i]] = channels[i]
        data = pd.Panel(d)
        return [data,t]
    

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

    #d[datalabels[dataindex]].set_value(cycleindex,col_labels,wholetc[col_labels].iloc[i])

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

def readEP(filename,datalabels):
    excelraw = pd.read_excel(filename)
    idx = [string.uppercase[i] for i in range(8)]
    x = range(12)
    cols = [col+1 for col in x]

    data = {dl:None for dl in datalabels}
    counter = 0
    for ind in excelraw.index:
        if excelraw.iloc[ind,0] == '<>':
            rawplate = excelraw.iloc[ind+1:ind+9,1:13].values
            data[datalabels[counter]] = pd.DataFrame(rawplate,idx,cols)
            counter += 1

    return data

def computegrowthrate(OD,t):
    #Calculate the growth rate in doublings per hour

    #One step
    onestep = pd.DataFrame(index = OD.index[0:-1], columns = OD.columns)
    for idx, index in enumerate(OD.index[0:-1]):
        ODdiff = (OD.iloc[idx+1,:]-OD.iloc[idx,:])
        tdiff = t[idx+1]-t[idx]
        onestep.set_value(index, OD.columns, ODdiff/tdiff)

    #Two step
    twostep = pd.DataFrame(index = OD.index[0:-2], columns = OD.columns)
    for idx, index in enumerate(OD.index[0:-2]):
        ODdiff = (OD.iloc[idx+2,:]-OD.iloc[idx,:])
        tdiff = t[idx+2]-t[idx]
        twostep.set_value(index, OD.columns, ODdiff/tdiff)

    #Find the max growth rate for each well

    maxind = twostep.idxmax()

    maxgrowth = twostep.max()

    maxOD = OD.max()

    return [twostep, maxind, maxgrowth, maxOD]

def exponentialvalues(maxind,vals):
    idx = [string.uppercase[i] for i in range(8)]
    x = range(12)
    cols = [col+1 for col in x]

    plate = pd.DataFrame(index = idx, columns = cols)

    for i in idx:
        for j in cols:
            index = i + str(j)
            if math.isnan(maxind[index]):
                plate.set_value(i,j,np.nan)
            else:
                plate.set_value(i,j,np.nanmean([vals.loc[int(maxind[index])-1,index],vals.loc[int(maxind[index]),index],vals.loc[int(maxind[index])+1,index]]))
    return plate

def tptoplate(cycle,df):
    #takes a cycle number (or an array of cycle numbers) and generates a 96 well plate formatted array from the data
    idx = [string.uppercase[i] for i in range(8)]
    x = range(12)
    cols = [col+1 for col in x]

    plate = pd.DataFrame(index = idx, columns = cols)

    if type(cycle) == int:
        for i in idx:
            for j in cols:
                index = i + str(j)
                plate.set_value(i,j,df.loc[cycle-1,index])
    else:
        for i in idx:
            for j in cols:
                index = i + str(j)
                plate.set_value(i,j,df.loc[cycle[i*12+j]-1,index])

    return plate
