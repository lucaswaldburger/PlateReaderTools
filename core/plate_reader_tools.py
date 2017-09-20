#Plate Reader Tools

import numpy as np
import pandas as pd
import math
import matplotlib.pyplot as plt
import string
from itertools import chain

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
                
    #use .any to report when "OVER" is present
    #replace "OVER" with np.nan .replace
    
    return [d,t]

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
    
def subplot_array(input_data, well_arr, time_list,axis_arr = []):
    #input_data is a pandas dataframe with wells for columns and with each row as a time point. 
    #The data does not have to have the actual times as the index .
    #
    #well_arr is an NP array with the names of the wells (e.g. 'A1') in the location in which
    #you want to plot the data. 
    #
    #time_list is an np array with each entry as a time point in whatever units you use. 
    #readplate returns time in units of hours. 
    #
    #axis_arr allows you to pass an array of axes to the function and use that. 
    nrows = int(well_arr.shape[0])
    ncols = int(well_arr.shape[1])
    fig, axarr = plt.subplots(nrows,ncols, sharex=True, sharey=True)
    
    #axarr[0, 0].plot(x, y)
    for jj in range(nrows):
        for kk in range(ncols): 
            yy = input_data[well_arr[jj,kk]]
            axarr[jj, kk].plot(time_list, yy)
            axarr[jj, kk].set_title(well_arr[jj,kk])
            if axis_arr != []:
                axarr[jj, kk].axis(axis_vec)
    
    return fig


def well_array_builder(letter_range,number_range):
    #letter_range is a list of letters that you want to be part of the array
    # e.g. ['A','B','C'].  They will appear as rows. 
    #number_range is a list of number taht you want to be part of the array
    #not necessarily consecutive: ['1','4','3'].  They will appear as columns. 
    wells = []    
    for jj in range(len(letter_range)):
        well_cols = []
        for kk in range(len(number_range)):
            well_cols.append(letter_range[jj]+str(number_range[kk]))
        wells.append(well_cols)
    well_arr = np.array(wells)
    
    return well_arr

def over_filter(input_dataframe):
    #input is the dataframe you want to filter OVER values out of.  
    #note: it is not the panel of dataframes.
    OVER_list = [index for (index, value) in input_dataframe.isin(['OVER']).any().iteritems() if value] 
    if len(OVER_list)==0:
        print('No OVER values in data')
        data_filtered = input_dataframe
    else: 
        print('OVER value found in well(s): \n' + '\n'.join(OVER_list))
        data_filtered = input_dataframe.replace('OVER',np.nan)
    return data_filtered, OVER_list
    
def view_or_input_exp_design(data_index):
    view_or_input = input("print out list (1) or add wells one by one (2)")

    if view_or_input =="1": 
        for jj in range(0,len(data_index.labels[0])):
            levels = data_index.levels
            labels = data_index.labels
            condition_description = []
            for kk in range(0,len(labels)): 
                condition_description.append(levels[kk][labels[kk][jj]])    
            print(condition_description)
        return
    elif view_or_input == "2": 
        class BreakIt(Exception): pass
    
        try:     
            well_list = []
            for jj in range(0,len(data_index.labels[0])):
                input_accepted = "0" 
                while input_accepted=="0":
                    levels = data_index.levels
                    labels = data_index.labels
                    condition_description = []
                    for kk in range(0,len(labels)): 
                        condition_description.append(levels[kk][labels[kk][jj]])    
                    new_well = input("input well for " + str(condition_description) + " : ")
                    input_accepted = input("correct well: " + new_well + "? 1=Yes, 0 = No, exit = break loop")
                    if input_accepted =="exit":
                        print("exiting loop")
                        raise BreakIt
                well_list.append(new_well)
                print(well_list)
        except BreakIt:
            pass  
        return well_list  
    else: 
        print("Didn't pick 1 or 2")
    
    
def delete_multiindex_for_missing_conditions(missing_items, data_index):
    #gives a new multiindex from a full multiindex with specified missing conditions. 
    #missing items is a list of tuples.  The tuples are of the form: 
    #(Level1,Item missing from level 1, Level2, Item missing from level 2)
    #for instance if strain ABC is missing technical replicate 3, you would put: 
    #("strain", "ABC", "tech_rep", "TR3") 
    
    inds_to_remove = []
    for missing_item in missing_items: 
        missing_cat1 = missing_item[0]
        missing_cat2 = missing_item[2]
        missing_cat1_ind = [i for i,name in enumerate(data_index.names) if name == missing_cat1][0]
        missing_cat2_ind = [i for i,name in enumerate(data_index.names) if name == missing_cat2][0]
        missing_item1 = missing_item[1]
        missing_item2 = missing_item[3]
        missing_item1_ind = [i for i,name in enumerate(data_index.levels[missing_cat1_ind]) if name == missing_item1][0]
        missing_item2_ind = [i for i,name in enumerate(data_index.levels[missing_cat2_ind]) if name == missing_item2][0]
        combined_labels = list(zip(data_index.labels[missing_cat1_ind],data_index.labels[missing_cat2_ind]))
        inds_to_remove_for_missing_item = [i for i,label in enumerate(combined_labels) if (label[0]==missing_item1_ind) and (label[1]==missing_item2_ind)]
        inds_to_remove.append(inds_to_remove_for_missing_item)
    
    #flatten out list of indices and remove duplicates. 
    inds_to_remove = list(set(chain.from_iterable(inds_to_remove)))
    
    new_labels =  [(np.delete(label_level,inds_to_remove)) for label_level in data_index.labels]
    data_index_adjusted = pd.MultiIndex(levels = data_index.levels, labels = new_labels , names = data_index.names)
    
    return data_index_adjusted, inds_to_remove
    
def get_slope(series):
    #returns the slope of a line when the x axis is the indices of a series and the 
    #y axis is the values. 
    t = series.index
    lst_sqrs_mat = np.vstack([t, np.ones(len(t))]).T
    slope, intercept = np.linalg.lstsq(lst_sqrs_mat, series)[0]

    
    return slope 