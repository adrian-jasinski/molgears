# -*- coding: utf-8 -*-
import xlrd
from datetime import datetime
from numpy import array
from math import log10

def read_fullplate(filepath, concs):
    from math import fabs
    workbook = xlrd.open_workbook(filepath)
    worksheet = workbook.sheet_by_index(0)
    date_cell = worksheet.cell_value(28, 1)
    if date_cell =='':
        date_cell = worksheet.cell_value(29, 1)
    measure_date = datetime.strptime(str(date_cell), '%Y-%m-%d %H:%M:%S')
    temp = worksheet.cell_value(30, 1)
    if temp == '':
        temp = worksheet.cell_value(31, 1)
    temp = float(temp.split()[1])
    matrix = [[0 for x in range(10)] for y in range(8)]             #macierz danych
    bg_matrix = [[0 for x in range(10)] for y in range(4)]           #dane srednie - komorki niebieskie - BG
    I = [] # pierwsza kolumna
    XII = [] #ostatnia kolumna
    f_list = [] #fluorescencja - lista
    fluorescence = 0
    curr_row = 33
    i=0
    while curr_row <= 40:
        curr_cell = 1
        j=0
        while curr_cell <= 12:
            cell_value = worksheet.cell_value(curr_row, curr_cell)
            if curr_cell == 1:
                I.append(float(cell_value))
            elif curr_cell == 12:
                XII.append(float(cell_value))
            else:
                matrix[i][j]=cell_value
                j+=1
            curr_cell+=1
        curr_row+=1
        i+=1
        
    I_avg = round(sum(I)/float(len(I)), 4)
    avg_col = array(matrix[4:]).T.mean(axis=1).tolist() # lista średnich wartości dla kontroli
    XII_avg = round(sum(XII[0:6])/float(len(XII[0:6])), 4)
    normal =[100*(el-XII_avg)/(I_avg-XII_avg) for el in avg_col]
    
    f_avg = 0.0                     #avarage number for caunting fluorescence
    for el in avg_col[5:]:
        f_avg += el/len(avg_col[5:])
    for el in avg_col:
        if fabs(el-f_avg)<11:
            f_list.append(1)
            fluorescence+=1
        else:
            f_list.append(0)
    x=0
    for row in matrix[0:4]:
        y=0
        for i in row:
            bg_matrix[x][y]=round(i-avg_col[y]+XII_avg, 4)
            y+=1
        x+=1
    C =[]
    C_BG =[]
    Ycontrol=[[]]*2
    for con in concs:
        Ycontrol[0].append(round(log10(con), 4))
    Ycontrol[1]=normal
    for el in range(len(concs)):
        C.append(round(log10(concs[int(el)]), 4))
    for el in range(len(concs)):
        C_BG.append(round(log10(concs[int(el)]), 4))
    ABCD =[]
    for row in matrix[:4]:
        list =[]
        for el in range(len(row)):
            list.append(round(100*(row[int(el)]-XII_avg)/(I_avg-XII_avg), 4))
        ABCD.append(list)
    BG_ABCD = []
    for row in bg_matrix:
        list =[]
        for el in range(len(row)):
            list.append( round(100*(row[int(el)]-XII_avg)/(I_avg-XII_avg), 4))
        BG_ABCD.append(list)
    return(C, C_BG, ABCD, BG_ABCD, Ycontrol, measure_date, temp, fluorescence, I_avg, XII_avg, f_list)

# +++++++++++++++++++++++++++++ read top of plate ++++++++++++++++++++++++++++++++
####################################################
def read_topplate(filepath, concs):
    workbook = xlrd.open_workbook(filepath)
    worksheet = workbook.sheet_by_index(0)
#    print "dir(worksheet)", dir(worksheet)
#    print "worksheet.sheet_selected", worksheet.name
    date_cell = worksheet.cell_value(28, 1)
    measure_date = datetime.strptime(str(date_cell), '%Y-%m-%d %H:%M:%S')
    temp = worksheet.cell_value(30, 1)
    temp = float(temp.split()[1])
    matrix = [[0 for x in range(10)] for y in range(8)]             #macierz danych kolumna II-XI
    bg_matrix = [[0 for x in range(10)] for y in range(3)]           #dane srednie - komorki niebieskie - BG
    I = [] # pierwsza kolumna
    XII = [] #ostatnia kolumna
    f_list = [] #fluorescencja - lista
    fluorescence = 0
    curr_row = 33
    i=0
    assert worksheet.cell_value(33, 0) == 'A'
    while curr_row <= 40:
        curr_cell = 1
        j=0
        while curr_cell <= 12:
            cell_value = worksheet.cell_value(curr_row, curr_cell)
#            print i, j, curr_cell, curr_row, worksheet.cell_value(curr_row, curr_cell), '\n'
            if curr_cell == 1:
                I.append(cell_value)
            elif curr_cell == 12:
                XII.append(cell_value)
            else:
                matrix[i][j]=cell_value
                j+=1
            curr_cell+=1
        curr_row+=1
        i+=1

    I_avg=round(sum(I)/float(len(I)), 4)                             #średnia wartość dla liczb z kolumny 1
    avg_col = array(matrix[3:4]).T.mean(axis=1).tolist() # lista średnich wartości dla kontroli
    XII_avg=round(sum(XII[0:6])/float(len(XII[0:6])), 4)    #średnia wartość dla liczb z kolumny 12
    normal =[100*(el-XII_avg)/(I_avg-XII_avg) for el in avg_col]
    
    
    f_avg = 0.0                     #avarage number for caunting fluorescence
    for el in avg_col[5:]:
        f_avg += el/len(avg_col[5:])
    from math import fabs
    nums = array(avg_col[5:])
    for el in avg_col:
#        if fabs(el-f_avg)<2.5*nums.std():
        if fabs(el-f_avg)<11:
            f_list.append(1)
            fluorescence+=1
        else:
            f_list.append(0)

    x=0                             #obliczanie danych dla tabeli - BG (niebieska z excela)
    for row in matrix[0:3]:
        y=0
        for i in row:
            bg_matrix[x][y]=round(i-avg_col[y]+XII_avg, 4)
            y+=1
        x+=1
    
                  #obliczanie log10 z listy stężeń (kolumna C)
    C =[]
    C_BG =[]
    Ycontrol=[[]]*2
    for con in concs:
        Ycontrol[0].append(round(log10(con), 4))
    Ycontrol[1]=normal
    for el in range(len(concs)):
        C.append(round(log10(concs[int(el)]), 4))
    for el in range(len(concs)):
        C_BG.append(round(log10(concs[int(el)]), 4))
    ABCD =[]                                    #macierz zbudowana z kolumn a, b, c, d
    for row in matrix[:3]:
        list =[]
        for el in range(len(row)):
            list.append( round(100*(row[int(el)]-XII_avg)/(I_avg-XII_avg), 4))
        ABCD.append(list)
    BG_ABCD = []                        #macierz -BG zbudowana z kolumn a, b, c, d
    for row in bg_matrix:
        list =[]
        for el in range(len(row)):
            list.append( round(100*(row[int(el)]-XII_avg)/(I_avg-XII_avg), 4))
        BG_ABCD.append(list)
    return(C, C_BG, ABCD, BG_ABCD, Ycontrol, measure_date, temp, fluorescence, I_avg, XII_avg, f_list)

def read_bottomplate(filepath, concs):
    workbook = xlrd.open_workbook(filepath)
    worksheet = workbook.sheet_by_index(0)
    date_cell = worksheet.cell_value(28, 1)
    measure_date = datetime.strptime(str(date_cell), '%Y-%m-%d %H:%M:%S')
    temp = worksheet.cell_value(30, 1)
    temp = float(temp.split()[1])
    matrix = [[0 for x in range(10)] for y in range(8)]             #macierz danych kolumna II-XI
    bg_matrix = [[0 for x in range(10)] for y in range(3)]           #dane srednie - komorki niebieskie - BG
    I = [] # pierwsza kolumna
    XII = [] #ostatnia kolumna
    f_list = [] #fluorescencja - lista
    fluorescence = 0
    curr_row = 33
    i=0
    while curr_row <= 40:
        curr_cell = 1
        j=0
        while curr_cell <= 12:
            cell_value = worksheet.cell_value(curr_row, curr_cell)
#            print cell_value
            if curr_cell == 1:
                I.append(cell_value)
            elif curr_cell == 12:
                XII.append(cell_value)
            else:
                matrix[i][j]=cell_value
                j+=1
            curr_cell+=1
        curr_row+=1
        i+=1
#    print I
    I_avg=round(sum(I)/float(len(I)), 4)                             #średnia wartość dla liczb z kolumny 1
    avg_col = array(matrix[-1:]).T.mean(axis=1).tolist() # lista średnich wartości dla kontroli
    XII_avg=round(sum(XII[0:6])/float(len(XII[0:6])), 4)    #średnia wartość dla liczb z kolumny 12
    normal =[100*(el-XII_avg)/(I_avg-XII_avg) for el in avg_col]
    
    f_avg = 0.0                     #avarage number for caunting fluorescence
    for el in avg_col[5:]:
        f_avg += el/len(avg_col[5:])
#    print "f_avg", f_avg
    from math import fabs
    for el in avg_col:
#        print "el %s" % avg_col.index(el), el
        if fabs(el-f_avg)<11:
            f_list.append(1)
            fluorescence+=1
        else:
            f_list.append(0)
            
    x=0                             #obliczanie danych dla tabeli - BG (niebieska z excela)
    for row in matrix[4:-1]:
        y=0
        for i in row:
            bg_matrix[x][y]=round(i-avg_col[y]+XII_avg, 4)
            y+=1
        x+=1
    
    #obliczanie log10 z listy stężeń (kolumna C)
    C =[]
    C_BG =[]
    Ycontrol=[[]]*2
    for con in concs:
        Ycontrol[0].append(round(log10(con), 4))
    Ycontrol[1]=normal
    for el in range(len(concs)):
        C.append(round(log10(concs[int(el)]), 4))
    for el in range(len(concs)):
        C_BG.append(round(log10(concs[int(el)]), 4))
    ABCD =[]                                    #macierz zbudowana z kolumn a, b, c, d
    for row in matrix[4:-1]:
        list =[]
        for el in range(len(row)):
            list.append( round(100*(row[int(el)]-XII_avg)/(I_avg-XII_avg), 4))
        ABCD.append(list)
    BG_ABCD = []                        #macierz -BG zbudowana z kolumn a, b, c, d
    for row in bg_matrix:
        list =[]
        for el in range(len(row)):
            list.append(round(100*(row[int(el)]-XII_avg)/(I_avg-XII_avg), 4))
        BG_ABCD.append(list)
    return(C, C_BG, ABCD, BG_ABCD, Ycontrol, measure_date, temp, fluorescence, I_avg, XII_avg, f_list)
    
# +++++++++++++++++++++++++++++ read half of plate ++++++++++++++++++++++++++++++++
####################################################
def read_halfplate_top_peptide(filepath, concs):
    workbook = xlrd.open_workbook(filepath)
    worksheet = workbook.sheet_by_index(0)
    date_cell = worksheet.cell_value(28, 1)
    print 'date_cell', date_cell
    assert worksheet.cell_value(33, 0) == 'A'
    measure_date = datetime.strptime(str(date_cell), '%Y-%m-%d %H:%M:%S')
    temp = worksheet.cell_value(30, 1)
    temp = float(temp.split()[1])
    matrix = [[0 for x in range(10)] for y in range(4)]             #macierz danych kolumna II-XI
    bg_matrix = [[0 for x in range(10)] for y in range(3)]           #dane srednie - komorki niebieskie - BG
    I = [] # pierwsza kolumna
    XII = [] #ostatnia kolumna
    f_list = [] #fluorescencja - lista
    fluorescence = 0
    curr_row = 33
    i=0
    while curr_row <= 36:
        curr_cell = 1
        j=0
        while curr_cell <= 12:
            cell_value = worksheet.cell_value(curr_row, curr_cell)
            if curr_cell == 1:
                I.append(cell_value)
            elif curr_cell == 12:
                XII.append(cell_value)
            else:
                matrix[i][j]=cell_value
                j+=1
            curr_cell+=1
        curr_row+=1
        i+=1

    I_avg=round(sum(I)/float(len(I)), 4)                             #średnia wartość dla liczb z kolumny 1
    avg_col = array(matrix[3:4]).T.mean(axis=1).tolist() # lista średnich wartości dla kontroli
    XII_avg=round(sum(XII[0:3])/float(len(XII[0:3])), 4)    #średnia wartość dla liczb z kolumny 12
    normal =[100*(el-XII_avg)/(I_avg-XII_avg) for el in avg_col]
    
    f_avg = 0.0                     #avarage number for caunting fluorescence
    for el in avg_col[5:]:
        f_avg += el/len(avg_col[5:])
    from math import fabs
    nums = array(avg_col[5:])
    for el in avg_col:
        if fabs(el-f_avg)<2.5*nums.std():
            f_list.append(1)
            fluorescence+=1
        else:
            f_list.append(0)

    x=0                             #obliczanie danych dla tabeli - BG (niebieska z excela)
    for row in matrix[0:3]:
        y=0
        for i in row:
            bg_matrix[x][y]=round(i-avg_col[y]+XII_avg, 4)
            y+=1
        x+=1
    
                  #obliczanie log10 z listy stężeń (kolumna C)
    C =[]
    C_BG =[]
    Ycontrol=[[]]*2
    for con in concs:
        Ycontrol[0].append(round(log10(con), 4))
    Ycontrol[1]=normal
    for el in range(len(concs)):
        C.append(round(log10(concs[int(el)]), 4))
    for el in range(len(concs)):
        C_BG.append(round(log10(concs[int(el)]), 4))
    ABCD =[]                                    #macierz zbudowana z kolumn a, b, c, d
    for row in matrix[:3]:
        list =[]
        for el in range(len(row)):
            list.append( round(100*(row[int(el)]-XII_avg)/(I_avg-XII_avg), 4))
        ABCD.append(list)
    BG_ABCD = []                        #macierz -BG zbudowana z kolumn a, b, c, d
    for row in bg_matrix:
        list =[]
        for el in range(len(row)):
            list.append( round(100*(row[int(el)]-XII_avg)/(I_avg-XII_avg), 4))
        BG_ABCD.append(list)
    return(C, C_BG, ABCD, BG_ABCD, Ycontrol, measure_date, temp, fluorescence, I_avg, XII_avg, f_list)
    
def read_halfplate_top_protein(filepath, concs):
    workbook = xlrd.open_workbook(filepath)
    worksheet = workbook.sheet_by_index(0)
    date_cell = worksheet.cell_value(28, 1)
    print 'date_cell', date_cell
    assert worksheet.cell_value(33, 0) == 'A'
    measure_date = datetime.strptime(str(date_cell), '%Y-%m-%d %H:%M:%S')
    temp = worksheet.cell_value(30, 1)
    temp = float(temp.split()[1])
    matrix = [[0 for x in range(10)] for y in range(4)]             #macierz danych kolumna II-XI
    bg_matrix = [[0 for x in range(10)] for y in range(3)]           #dane srednie - komorki niebieskie - BG
    I = [] # pierwsza kolumna
    XII = [] #ostatnia kolumna
    f_list = [] #fluorescencja - lista
    fluorescence = 0
    curr_row = 33
    # kolumna XII
    while curr_row <= 40:
        cell_value = worksheet.cell_value(curr_row, 12)
        XII.append(cell_value)
        curr_row+=1
    
    curr_row = 33
    i=0        
    while curr_row <= 36:
        curr_cell = 1
        j=0
        while curr_cell <= 12:
            cell_value = worksheet.cell_value(curr_row, curr_cell)
            if curr_cell == 1:
                I.append(cell_value)
            elif curr_cell == 12:
                pass
            else:
                matrix[i][j]=cell_value
                j+=1
            curr_cell+=1
        curr_row+=1
        i+=1

    I_avg=round(sum(I)/float(len(I)), 4)                             #średnia wartość dla liczb z kolumny 1
    avg_col = array(matrix[3:4]).T.mean(axis=1).tolist() # lista średnich wartości dla kontroli
    XII_avg=round(sum(XII[0:6])/float(len(XII[0:6])), 4)    #średnia wartość dla liczb z kolumny 12
    normal =[100*(el-XII_avg)/(I_avg-XII_avg) for el in avg_col]
    
    f_avg = 0.0                     #avarage number for caunting fluorescence
    for el in avg_col[5:]:
        f_avg += el/len(avg_col[5:])
    from math import fabs
    nums = array(avg_col[5:])
    for el in avg_col:
        if fabs(el-f_avg)<2.5*nums.std():
            f_list.append(1)
            fluorescence+=1
        else:
            f_list.append(0)

    x=0                             #obliczanie danych dla tabeli - BG (niebieska z excela)
    for row in matrix[0:3]:
        y=0
        for i in row:
            bg_matrix[x][y]=round(i-avg_col[y]+XII_avg, 4)
            y+=1
        x+=1
    
                  #obliczanie log10 z listy stężeń (kolumna C)
    C =[]
    C_BG =[]
    Ycontrol=[[]]*2
    for con in concs:
        Ycontrol[0].append(round(log10(con), 4))
    Ycontrol[1]=normal
    for el in range(len(concs)):
        C.append(round(log10(concs[int(el)]), 4))
    for el in range(len(concs)):
        C_BG.append(round(log10(concs[int(el)]), 4))
    ABCD =[]                                    #macierz zbudowana z kolumn a, b, c, d
    for row in matrix[:3]:
        list =[]
        for el in range(len(row)):
            list.append( round(100*(row[int(el)]-XII_avg)/(I_avg-XII_avg), 4))
        ABCD.append(list)
    BG_ABCD = []                        #macierz -BG zbudowana z kolumn a, b, c, d
    for row in bg_matrix:
        list =[]
        for el in range(len(row)):
            list.append( round(100*(row[int(el)]-XII_avg)/(I_avg-XII_avg), 4))
        BG_ABCD.append(list)
    return(C, C_BG, ABCD, BG_ABCD, Ycontrol, measure_date, temp, fluorescence, I_avg, XII_avg, f_list)


def read_halfplate_bottom_peptide(filepath, concs):
    workbook = xlrd.open_workbook(filepath)
    worksheet = workbook.sheet_by_index(0)
    date_cell = worksheet.cell_value(28, 1)
    measure_date = datetime.strptime(str(date_cell), '%Y-%m-%d %H:%M:%S')
    temp = worksheet.cell_value(30, 1)
    temp = float(temp.split()[1])
    matrix = [[0 for x in range(10)] for y in range(4)]             #macierz danych kolumna II-XI
    bg_matrix = [[0 for x in range(10)] for y in range(3)]           #dane srednie - komorki niebieskie - BG
    I = [] # pierwsza kolumna
    XII = [] #ostatnia kolumna
    f_list = [] #fluorescencja - lista
    fluorescence = 0
    curr_row = 34
    i=0
    while curr_row <= 37:
        curr_cell = 1
        j=0
        while curr_cell <= 12:
            cell_value = worksheet.cell_value(curr_row, curr_cell)
            if curr_cell == 1:
                I.append(cell_value)
            elif curr_cell == 12:
                XII.append(cell_value)
            else:
                matrix[i][j]=cell_value
                j+=1
            curr_cell+=1
        curr_row+=1
        i+=1
    
    I_avg=round(sum(I)/float(len(I)), 4)                             #średnia wartość dla liczb z kolumny 1
    avg_col = array(matrix[3:4]).T.mean(axis=1).tolist() # lista średnich wartości dla kontroli
    XII_avg=round(sum(XII[0:2])/float(len(XII[0:2])), 4)    #średnia wartość dla liczb z kolumny 12
    normal =[100*(el-XII_avg)/(I_avg-XII_avg) for el in avg_col]
    
    f_avg = 0.0                     #avarage number for caunting fluorescence
    for el in avg_col[5:]:
        f_avg += el/len(avg_col[5:])
    from math import fabs
    nums = array(avg_col[5:])
    for el in avg_col:
        if fabs(el-f_avg)<2.5*nums.std():
            f_list.append(1)
            fluorescence+=1
        else:
            f_list.append(0)
            
    x=0                             #obliczanie danych dla tabeli - BG (niebieska z excela)
    for row in matrix[0:3]:
        y=0
        for i in row:
            bg_matrix[x][y]=round(i-avg_col[y]+XII_avg, 4)
            y+=1
        x+=1
    
                  #obliczanie log10 z listy stężeń (kolumna C)
    C =[]
    C_BG =[]
    Ycontrol=[[]]*2
    for con in concs:
        Ycontrol[0].append(round(log10(con), 4))
    Ycontrol[1]=normal
    for el in range(len(concs)):
        C.append(round(log10(concs[int(el)]), 4))
    for el in range(len(concs)):
        C_BG.append(round(log10(concs[int(el)]), 4))
    ABCD =[]                                    #macierz zbudowana z kolumn a, b, c, d
    for row in matrix[:3]:
        list =[]
        for el in range(len(row)):
            list.append( round(100*(row[int(el)]-XII_avg)/(I_avg-XII_avg), 4))
        ABCD.append(list)
    BG_ABCD = []                        #macierz -BG zbudowana z kolumn a, b, c, d
    for row in bg_matrix:
        list =[]
        for el in range(len(row)):
            list.append( round(100*(row[int(el)]-XII_avg)/(I_avg-XII_avg), 4))
        BG_ABCD.append(list)
    return(C, C_BG, ABCD, BG_ABCD, Ycontrol, measure_date, temp, fluorescence, I_avg, XII_avg, f_list)
    
def read_halfplate_bottom_protein(filepath, concs):
    workbook = xlrd.open_workbook(filepath)
    worksheet = workbook.sheet_by_index(0)
    date_cell = worksheet.cell_value(28, 1)
    print 'date_cell', date_cell
    measure_date = datetime.strptime(str(date_cell), '%Y-%m-%d %H:%M:%S')
    temp = worksheet.cell_value(30, 1)
    temp = float(temp.split()[1])
    matrix = [[0 for x in range(10)] for y in range(4)]             #macierz danych kolumna II-XI
    bg_matrix = [[0 for x in range(10)] for y in range(3)]           #dane srednie - komorki niebieskie - BG
    I = [] # pierwsza kolumna
    XII = [] #ostatnia kolumna
    f_list = [] #fluorescencja - lista
    fluorescence = 0
    
    #kolumna XII
    curr_row = 33
    i=0
    while curr_row <= 40:
        curr_cell = 1
        j=0
        while curr_cell <= 12:
            cell_value = worksheet.cell_value(curr_row, curr_cell)
            if curr_cell == 12:
                XII.append(cell_value)
                j+=1
            curr_cell+=1
        curr_row+=1
        i+=1
    
    #pozostała macierz
    curr_row = 37
    i=0
    while curr_row <= 40:
        curr_cell = 1
        j=0
        while curr_cell <= 12:
            print 'row', curr_row, 'cel', curr_cell
            cell_value = worksheet.cell_value(curr_row, curr_cell)
            print 'val', cell_value
            if curr_cell == 1:
                I.append(cell_value)
            elif curr_cell == 12:
                pass
            else:
                matrix[i][j]=cell_value
                j+=1
            curr_cell+=1
        curr_row+=1
        i+=1

    print 'matrix', matrix
    print 'I', I
    I_avg=round(sum(I)/float(len(I)), 4)                             #średnia wartość dla liczb z kolumny 1
    avg_col = array(matrix[3:4]).T.mean(axis=1).tolist() # lista średnich wartości dla kontroli
    XII_avg=round(sum(XII[0:6])/float(len(XII[0:6])), 4)    #średnia wartość dla liczb z kolumny 12
    normal =[100*(el-XII_avg)/(I_avg-XII_avg) for el in avg_col]
    
    f_avg = 0.0                     #avarage number for caunting fluorescence
    for el in avg_col[5:]:
        f_avg += el/len(avg_col[5:])
    from math import fabs
    nums = array(avg_col[5:])
    for el in avg_col:
        if fabs(el-f_avg)<2.5*nums.std():
            f_list.append(1)
            fluorescence+=1
        else:
            f_list.append(0)
            
    x=0                             #obliczanie danych dla tabeli - BG (niebieska z excela)
    for row in matrix[0:3]:
        y=0
        for i in row:
            bg_matrix[x][y]=round(i-avg_col[y]+XII_avg, 4)
            y+=1
        x+=1
    
                  #obliczanie log10 z listy stężeń (kolumna C)
    C =[]
    C_BG =[]
    Ycontrol=[[]]*2
    for con in concs:
        Ycontrol[0].append(round(log10(con), 4))
    Ycontrol[1]=normal
    for el in range(len(concs)):
        C.append(round(log10(concs[int(el)]), 4))
    for el in range(len(concs)):
        C_BG.append(round(log10(concs[int(el)]), 4))
    ABCD =[]                                    #macierz zbudowana z kolumn a, b, c, d
    for row in matrix[:3]:
        list =[]
        for el in range(len(row)):
            list.append( round(100*(row[int(el)]-XII_avg)/(I_avg-XII_avg), 4))
        ABCD.append(list)
    BG_ABCD = []                        #macierz -BG zbudowana z kolumn a, b, c, d
    for row in bg_matrix:
        list =[]
        for el in range(len(row)):
            list.append( round(100*(row[int(el)]-XII_avg)/(I_avg-XII_avg), 4))
        BG_ABCD.append(list)
    return(C, C_BG, ABCD, BG_ABCD, Ycontrol, measure_date, temp, fluorescence, I_avg, XII_avg, f_list)

    
# +++++++++++++++read palte layaut 3+5++++++++++++++++++++++++++
def read_3_5_plate(filepath, concs):
    workbook = xlrd.open_workbook(filepath)
    worksheet = workbook.sheet_by_index(0)
    date_cell = worksheet.cell_value(28, 1)
    if date_cell =='':
        date_cell = worksheet.cell_value(29, 1)
    measure_date = datetime.strptime(str(date_cell), '%Y-%m-%d %H:%M:%S')
    temp = worksheet.cell_value(30, 1)
    if temp == '':
        temp = worksheet.cell_value(31, 1)
    temp = float(temp.split()[1])
    matrix = [[0 for x in range(10)] for y in range(8)]             #macierz danych
    bg_matrix = [[0 for x in range(10)] for y in range(3)]           #dane srednie - komorki niebieskie - BG
    I = [] # pierwsza kolumna
    XII = [] #ostatnia kolumna
    f_list = [] #fluorescencja - lista
    fluorescence = 0
    curr_row = 33
    i=0
    while curr_row <= 40:
        curr_cell = 1
        j=0
        while curr_cell <= 12:
            cell_value = worksheet.cell_value(curr_row, curr_cell)
            if curr_cell == 1:
                I.append(float(cell_value))
            elif curr_cell == 12:
                XII.append(float(cell_value))
            else:
                matrix[i][j]=cell_value
                j+=1
            curr_cell+=1
        curr_row+=1
        i+=1
    
    I_avg=round(sum(I)/float(len(I)), 4)                             #średnia wartość dla liczb z kolumny 1
    avg_col = array(matrix[3:]).T.mean(axis=1).tolist() # lista średnich wartości dla kontroli
    XII_avg=round(sum(XII[0:6])/float(len(XII[0:6])), 4)    #średnia wartość dla liczb z kolumny 12
    normal =[100*(el-XII_avg)/(I_avg-XII_avg) for el in avg_col]
    
    f_avg = 0.0                     #avarage number for caunting fluorescence
    for el in avg_col[5:]:
        f_avg += el/len(avg_col[5:])
    from math import fabs
    for el in avg_col:
        if fabs(el-f_avg)<11:
            f_list.append(1)
            fluorescence+=1
        else:
            f_list.append(0)

    x=0
    for row in matrix[0:3]:
        y=0
        for i in row:
            bg_matrix[x][y]=round(i-avg_col[y]+XII_avg, 4)
            y+=1
        x+=1
    
    C =[]
    C_BG =[]
    Ycontrol=[[]]*2
    for con in concs:
        Ycontrol[0].append(round(log10(con), 4))
    Ycontrol[1]=normal
    for el in range(len(concs)):
        C.append(round(log10(concs[int(el)]), 4))
    for el in range(len(concs)):
        C_BG.append(round(log10(concs[int(el)]), 4))
    ABCD =[]
    for row in matrix[:3]:
        list =[]
        for el in range(len(row)):
            list.append(round(100*(row[int(el)]-XII_avg)/(I_avg-XII_avg), 4))
        ABCD.append(list)
    BG_ABCD = []
    for row in bg_matrix:
        list =[]
        for el in range(len(row)):
            list.append(round(100*(row[int(el)]-XII_avg)/(I_avg-XII_avg), 4))
        BG_ABCD.append(list)
    return(C, C_BG, ABCD, BG_ABCD, Ycontrol, measure_date, temp, fluorescence, I_avg, XII_avg, f_list)

## +++++++++++++++ Zapisz Dane ++++++++++++++++++++++++++
# X  - macierz X
# X_BG  - macierz X -BG
# ABCD -macierz wyników RAW
# ABCD_BG - macierz wyników RAW - BG
#filepath - scieżka do pliku graficznego png
def save_fix_data(CX, CX_BG, Y_ABCD, Y_ABCD_BG, Ycontrol, test, filepath, scope, scope_BG, f_list, raw, dpi=None):
    from pylab import plot, title, xlabel, ylabel, legend, axes, text, savefig, grid, clf, gca, axvline, axhline, setp, errorbar, close
    from scipy import optimize, linspace
    from math import fabs
    from numpy import mean
    
    #create thumb file name:
    import os
    head, tail = os.path.split(filepath)        
    thumbpath = os.path.join(head, "thumb_"+tail)
        
    
    props = dict(boxstyle='square', facecolor='white')
    X = []
    X_BG = []
    ABCD = []
    ABCD_BG = []
    for el in scope:
        X.append(CX[int(el)-1])
    for el in scope_BG:
        X_BG.append(CX_BG[int(el)-1])
        
    for row in Y_ABCD:
        list =[]
        for el in scope:
            list.append(row[int(el)-1])
        ABCD.append(list)
    for row in Y_ABCD_BG:
        list =[]
        for el in scope_BG:
            list.append(row[int(el)-1])
        ABCD_BG.append(list)
    
    x = X
    x_bg = X_BG
    nums =  array(ABCD).T
    nums_BG =  array(ABCD_BG).T
    ALL_nums = array(Y_ABCD).T
    ALL_nums_BG = array(Y_ABCD_BG).T
    # STDEV
    Yerr = nums.std(axis=1)
    Y_BGerr = nums_BG.std(axis=1)
    # Means from array
    y = nums.mean(axis=1).tolist()
    y_bg = nums_BG.mean(axis=1).tolist()
    ALL_y = ALL_nums.mean(axis=1).tolist()
    ALL_y_bg = ALL_nums_BG.mean(axis=1).tolist()

    hi = int(round(max(x)+2, 0))
    lo = int(round(min(x), 0))-1
    p0_gess = CX[int((len(CX)/2)-1)]
    p0 = [p0_gess,-1.]
    Top = 100
    Bottom = 0
    
    out_of_scale = []
    out_of_scale_BG = []
    
    sections = {} # dict of lists of y.index(el) - for ranges(1,7): >90 | 90-75 | 75-50 | 50-25 | 25-10 | <10
    for el in y:
        if el > 120.0:
            out_of_scale.append((X[y.index(el)], round(el, 4)))
            sections.setdefault(6, []).append(y.index(el))
        elif el > 90.0:
            sections.setdefault(6, []).append(y.index(el))
        elif el <= 90.0 and el > 75.0:
            sections.setdefault(5, []).append(y.index(el))
        elif el <= 75.0 and el > 50.0:
            sections.setdefault(4, []).append(y.index(el))
        elif el <= 50.0 and el > 25.0:
            sections.setdefault(3, []).append(y.index(el))
        elif el <= 25.0 and el > 10.0:
            sections.setdefault(2, []).append(y.index(el))
        elif el <= 10.0 and  el >= -20.0:
            sections.setdefault(1, []).append(y.index(el))
        elif  el < -20.0:
            out_of_scale.append((X[y.index(el)], round(el, 4)))
            sections.setdefault(1, []).append(y.index(el))
    sections_BG = {} # dict of lists of y.index(el) - for ranges(1,7): >90 | 90-75 | 75-50 | 50-25 | 25-10 | <10
    for el in y_bg:
        if el > 120.0:
            out_of_scale_BG.append((X_BG[y_bg.index(el)], round(el, 4)))
            sections_BG.setdefault(6, []).append(y_bg.index(el))
        elif el > 90.0:
            sections_BG.setdefault(6, []).append(y_bg.index(el))
        elif el <= 90.0 and el > 75.0:
            sections_BG.setdefault(5, []).append(y_bg.index(el))
        elif el <= 75.0 and el > 50.0:
            sections_BG.setdefault(4, []).append(y_bg.index(el))
        elif el <= 50.0 and el > 25.0:
            sections_BG.setdefault(3, []).append(y_bg.index(el))
        elif el <= 25.0 and el > 10.0:
            sections_BG.setdefault(2, []).append(y_bg.index(el))
        elif el <= 10.0 and  el >= -20.0:
            sections_BG.setdefault(1, []).append(y_bg.index(el))
        elif  el < -20.0:
            out_of_scale_BG.append((X_BG[y_bg.index(el)], round(el, 4)))
            sections_BG.setdefault(1, []).append(y_bg.index(el))
    for el in y_bg:
        if el > 120.0 or el < -20.0:
            out_of_scale_BG.append((X_BG[y_bg.index(el)], round(el, 4)))
            
    keys = []
    fluorescence = 0
    if raw:
        selected_section = sections
    else:
        selected_section = sections_BG
    for k, v in selected_section.iteritems():
        if len(v)>0:
            keys.append(k)
    k_min = min(keys)
    k_max = max(keys)
    fluorescence += k_max-k_min
    for k, v in selected_section.iteritems():
        if len(v)>0:
            test_me = True
            for vx in v:
                if f_list[vx] == 0:
                    test_me = False
            if test_me:
                fluorescence+=1
        else:
            if k<k_max and k>k_min:
                fluorescence+=1
    
    fitfunc = lambda p,X : Bottom + (Top-Bottom)/ (1+10**((p[0]-X)*p[1]))
    errfunc = lambda p, x, y: fitfunc(p, x) - y # Distance to the target function
    p1,cov,infodict,mesg,ier = optimize.leastsq(errfunc, p0[:], args=(x, y), full_output=True)
    ss_err=(infodict['fvec']**2).sum()
    ss_tot=((y-mean(y))**2).sum()
    Rsquared=1-(ss_err/ss_tot)

    p1_bg ,cov_bg,infodict_bg,mesg_bg,ier_bg = optimize.leastsq(errfunc, p0[:], args=(x_bg, y_bg), full_output=True)
    ss_err_bg=(infodict_bg['fvec']**2).sum()
    ss_tot_bg=((y_bg-mean(y_bg))**2).sum()
    Rsquared_BG=1-(ss_err_bg/ss_tot_bg)
    
    x_range = linspace(hi, lo, 100)
    x_range_solid = linspace(X[-1], X[0], 100)
    graph1 = plot(Ycontrol[0], Ycontrol[1], "--", color="gray", label=None)
    errorbar(CX, ALL_y, yerr=None, fmt="o", color="lightblue", label=None)
    errorbar(x, y, yerr=Yerr, fmt="o", color="#003366", label=None)
    graph_solid= plot(x_range_solid, fitfunc(p1, x_range_solid), "-", color="#003366", label=None)
    graph_dotted= plot(x_range, fitfunc(p1, x_range), "--", color="#003366", label=None)
    title("Receptor binding - Fit logIC50")
    ylabel("inhibition [%]")
    res = p1[:]
    log_ic50 = res[0]
    res[0] = 10**p1[0]
    ki = (test.lb*res[0]*test.kd)/((test.lt*test.rt)+test.lb*(test.rt-test.lt+test.lb-test.kd))
#    if out_of_scale:
#        if res[0]>9999.0:
#            msg = 'IC50: >9999.0\nHS:      {: 7.3f}\noff-scale(x,y): {:}'.format(res[1], out_of_scale)
#        else:
#            msg = 'IC50: {: 7.3f}\nHS:      {: 7.3f}\noff-scale(x,y): {:}'.format(res[0], res[1], out_of_scale)
#    else:
#        if res[0]>9999.0:
#            msg = 'IC50: >9999.0\nHS:      {: 7.3f}'.format(res[1])
#        else:
#            msg = 'IC50: {: 7.3f}\nHS:      {: 7.3f}'.format(res[0], res[1])
    if res[0]>9999.0:
        msg = 'Ki:   >999.0\nIC50: >9999.0\nHS:      {: 7.3f}\nR2:      {: 7.3f}'.format(res[1], Rsquared)
    else:
        msg = 'Ki:      {: 7.3f}\nIC50: {: 7.3f}\nHS:      {: 7.3f}\nR2:      {: 7.3f}'.format(ki, res[0], res[1], Rsquared)
    text(lo+.05, 24,
         msg,
         fontsize=10,
         verticalalignment='bottom',
         color="#003366",
         alpha=1.0, 
         backgroundcolor="white" 
         )   
#    graph2 = plot(x_bg, y_bg, "ro", color="#006600", label="IC50 -BG")
    x_bg_range_solid = linspace(X_BG[-1], X_BG[0], 100)
    errorbar(CX_BG, ALL_y_bg, yerr=None, fmt='o', color="lightgreen", label=None)
    errorbar(x_bg, y_bg, yerr=Y_BGerr, fmt='o', color="#006600", label=None)
    graph2_solid = plot(x_bg_range_solid, fitfunc(p1_bg, x_bg_range_solid), "-", color="#006600", label=None)
    graph2_dotted = plot(x_range, fitfunc(p1_bg, x_range), "--", color="#006600", label=None)
    
    # Legend the plot
    xlabel(r"conc [log($\mu$M)]")
    ylabel("inhibition [%]")
    from matplotlib.lines import Line2D
    line = Line2D(range(10), range(10), linestyle='-', marker='o', color="#003366")
    line2 = Line2D(range(10), range(10), linestyle='-', marker='o', color="#006600")
    line3 = Line2D(range(10), range(10), linestyle='-', marker='.', color="gray")
    leg = legend((line, line2, line3, ), ('IC50', 'IC50 -BG', 'BG', ), loc=1)
    ltext  = leg.get_texts()
    setp(ltext, fontsize='small')
    
    res_bg = p1_bg[:]
    log_ic50_bg = res_bg[0]
    res_bg[0] = 10**p1_bg[0]
    ki_bg = (test.lb*res_bg[0]*test.kd)/((test.lt*test.rt)+test.lb*(test.rt-test.lt+test.lb-test.kd))
#    if out_of_scale_BG:
#        if res_bg[0]>9999.0:
#            msg_BG = 'IC50: >9999.0\nHS:      {: 7.3f}\noff-scale(x,y): {:}'.format(res_bg[1], out_of_scale_BG)
#        else:
#            msg_BG = 'IC50: {: 7.3f}\nHS:      {: 7.3f}\noff-scale(x,y): {:}'.format(res_bg[0], res_bg[1], out_of_scale_BG)
#    else:
#        if res_bg[0]>9999.0:
#            msg_BG = 'IC50: >9999.0\nHS:      {: 7.3f}'.format(res_bg[1])
#        else:
#            msg_BG = 'IC50: {: 7.3f}\nHS:      {: 7.3f}'.format(res_bg[0], res_bg[1])
    if res_bg[0]>9999.0:
        msg_BG = 'Ki:   >999.0\nIC50: >9999.0\nHS:      {: 7.3f}\nR2:      {: 7.3f}'.format(res_bg[1], Rsquared_BG)
    else:
        msg_BG = 'Ki:      {: 7.3f}\nIC50: {: 7.3f}\nHS:      {: 7.3f}\nR2:      {: 7.3f}'.format(ki_bg, res_bg[0], res_bg[1], Rsquared_BG)
    text(lo+.05, 2,
         msg_BG,
         fontsize=10,
         verticalalignment='bottom',
         color="#006600",
         alpha=1.0, 
         backgroundcolor="white" 
         )
    grid()
    ax = gca()
    ax.set_ylim(-20,120) #  
    ax.set_xlim(lo,hi) #  
    axvline(x=0, color="#2e7682")
    axhline(y=0, color="#2e7682")
    for item in ([ax.xaxis.label, ax.yaxis.label] +ax.get_xticklabels() + ax.get_yticklabels()):
        item.set_fontsize(10)
    if dpi:
        savefig(filepath, dpi=dpi)
    else:
        savefig(filepath)
        savefig(thumbpath, dpi=50)
    close()

    return((round(res[0], 4), round(res[1], 4), round(Rsquared, 4), round(ki, 4)), (round(res_bg[0], 4), round(res_bg[1], 4), round(Rsquared_BG, 4), round(ki_bg, 4)), fluorescence)

def save_data_fix_HS(CX, CX_BG, Y_ABCD, Y_ABCD_BG, Ycontrol, test, filepath, scope, scope_BG, f_list, raw, dpi=None):
    from pylab import plot, title, xlabel, ylabel, legend, axes, text, savefig, grid, clf, gca, axvline, axhline, setp, errorbar, close
    from scipy import optimize, linspace
    from math import fabs
    from numpy import mean
    
    import os
    head, tail = os.path.split(filepath)        
    thumbpath = os.path.join(head, "thumb_"+tail)
    
    props = dict(boxstyle='square', facecolor='white')
    X = []
    X_BG = []
    ABCD = []
    ABCD_BG = []
    for el in scope:
        X.append(CX[int(el)-1])
    for el in scope_BG:
        X_BG.append(CX_BG[int(el)-1])
        
    for row in Y_ABCD:
        list =[]
        for el in scope:
            list.append(row[int(el)-1])
        ABCD.append(list)
    for row in Y_ABCD_BG:
        list =[]
        for el in scope_BG:
            list.append(row[int(el)-1])
        ABCD_BG.append(list)
        
    x = X
    x_bg = X_BG
    nums =  array(ABCD).T
    nums_BG =  array(ABCD_BG).T
    ALL_nums = array(Y_ABCD).T
    ALL_nums_BG = array(Y_ABCD_BG).T
    # STDEV
    Yerr = nums.std(axis=1)
    Y_BGerr = nums_BG.std(axis=1)
    # Means from array
    y = nums.mean(axis=1).tolist()
    y_bg = nums_BG.mean(axis=1).tolist()
    ALL_y = ALL_nums.mean(axis=1).tolist()
    ALL_y_bg = ALL_nums_BG.mean(axis=1).tolist()

    hi = int(round(max(x)+2, 0))
    lo = int(round(min(x), 0))-1
    p0_gess = CX[int((len(CX)/2)-1)]
    p0 = [p0_gess]
    Top = 100
    Bottom = 0
    
    out_of_scale = []
    out_of_scale_BG = []
    sections = {} # dict of lists of y.index(el) - for ranges(1,7): >90 | 90-75 | 75-50 | 50-25 | 25-10 | <10
    for el in y:
        if el > 120.0:
            out_of_scale.append((X[y.index(el)], round(el, 4)))
            sections.setdefault(6, []).append(y.index(el))
        elif el > 90.0:
            sections.setdefault(6, []).append(y.index(el))
        elif el <= 90.0 and el > 75.0:
            sections.setdefault(5, []).append(y.index(el))
        elif el <= 75.0 and el > 50.0:
            sections.setdefault(4, []).append(y.index(el))
        elif el <= 50.0 and el > 25.0:
            sections.setdefault(3, []).append(y.index(el))
        elif el <= 25.0 and el > 10.0:
            sections.setdefault(2, []).append(y.index(el))
        elif el <= 10.0 and  el >= -20.0:
            sections.setdefault(1, []).append(y.index(el))
        elif  el < -20.0:
            out_of_scale.append((X[y.index(el)], round(el, 4)))
            sections.setdefault(1, []).append(y.index(el))
    sections_BG = {} # dict of lists of y.index(el) - for ranges(1,7): >90 | 90-75 | 75-50 | 50-25 | 25-10 | <10
    for el in y_bg:
        if el > 120.0:
            out_of_scale_BG.append((X_BG[y_bg.index(el)], round(el, 4)))
            sections_BG.setdefault(6, []).append(y_bg.index(el))
        elif el > 90.0:
            sections_BG.setdefault(6, []).append(y_bg.index(el))
        elif el <= 90.0 and el > 75.0:
            sections_BG.setdefault(5, []).append(y_bg.index(el))
        elif el <= 75.0 and el > 50.0:
            sections_BG.setdefault(4, []).append(y_bg.index(el))
        elif el <= 50.0 and el > 25.0:
            sections_BG.setdefault(3, []).append(y_bg.index(el))
        elif el <= 25.0 and el > 10.0:
            sections_BG.setdefault(2, []).append(y_bg.index(el))
        elif el <= 10.0 and  el >= -20.0:
            sections_BG.setdefault(1, []).append(y_bg.index(el))
        elif  el < -20.0:
            out_of_scale_BG.append((X_BG[y_bg.index(el)], round(el, 4)))
            sections_BG.setdefault(1, []).append(y_bg.index(el))
    for el in y_bg:
        if el > 120.0 or el < -20.0:
            out_of_scale_BG.append((X_BG[y_bg.index(el)], round(el, 4)))
            
    keys = []
    fluorescence = 0
    if raw:
        selected_section = sections
    else:
        selected_section = sections_BG
    for k, v in selected_section.iteritems():
        if len(v)>0:
            keys.append(k)
    k_min = min(keys)
    k_max = max(keys)
    fluorescence += k_max-k_min
    for k, v in selected_section.iteritems():
        if len(v)>0:
            test_me = True
            for vx in v:
                if f_list[vx] == 0:
                    test_me = False
            if test_me:
                fluorescence+=1
        else:
            if k<k_max and k>k_min:
                fluorescence+=1
    
    fitfunc = lambda p,X : Bottom + (Top-Bottom)/ (1+10**((p[0]-X)*(-1.)))
    errfunc = lambda p, x, y: fitfunc(p, x) - y # Distance to the target function
    p1,cov,infodict,mesg,ier = optimize.leastsq(errfunc, p0[:], args=(x, y), full_output=True)
    ss_err=(infodict['fvec']**2).sum()
    ss_tot=((y-mean(y))**2).sum()
    Rsquared=1-(ss_err/ss_tot)

    p1_bg ,cov_bg,infodict_bg,mesg_bg,ier_bg = optimize.leastsq(errfunc, p0[:], args=(x_bg, y_bg), full_output=True)
    ss_err_bg=(infodict_bg['fvec']**2).sum()
    ss_tot_bg=((y_bg-mean(y_bg))**2).sum()
    Rsquared_BG=1-(ss_err_bg/ss_tot_bg)
    
    x_range = linspace(hi, lo, 100)
    x_range_solid = linspace(X[-1], X[0], 100)
    graph1 = plot(Ycontrol[0], Ycontrol[1], "--", color="gray", label=None)
    errorbar(CX, ALL_y, yerr=None, fmt="o", color="lightblue", label=None)
    errorbar(x, y, yerr=Yerr, fmt="o", color="#003366", label=None)
    graph_solid= plot(x_range_solid, fitfunc(p1, x_range_solid), "-", color="#003366", label=None)
    graph_dotted= plot(x_range, fitfunc(p1, x_range), "--", color="#003366", label=None)
    
    title("Receptor binding - Fit logIC50")
    ylabel("inhibition [%]")
    res = p1[:]
    log_ic50 = res[0]
    res[0] = 10**p1[0]
    ki = (test.lb*res[0]*test.kd)/((test.lt*test.rt)+test.lb*(test.rt-test.lt+test.lb-test.kd))
#    if out_of_scale:
#        if res[0]>9999.0:
#            msg = 'IC50: >9999.0\noff-scale(x,y): {:}'.format(Rsq)
#        else:
#            msg = 'IC50: {: 7.3f}\noff-scale(x,y): {:}'.format(res[0], out_of_scale)
#    else:
#    if res[0]>9999.0:
#        msg = 'Ki:   >999.0\nIC50: >9999.0\nHS:      -1.0\nR2:      {: 7.3f}'.format(Rsquared)
#    else:
#        msg = 'Ki:      {: 7.3f}\nIC50: {: 7.3f}\nHS:      -1.0\nR2:      {: 7.3f}'.format(ki, res[0], Rsquared)
    if res[0]>9999.0:
        msg = 'Ki:   >999.0\nIC50: >9999.0\nHS:       -1.0\nR2:      {: 7.3f}'.format(Rsquared)
    else:
        msg = 'Ki:      {: 7.3f}\nIC50: {: 7.3f}\nHS:     -1.0\nR2:      {: 7.3f}'.format(ki, res[0], Rsquared)
    text(lo+.05, 24,
         msg,
         fontsize=10,
         verticalalignment='bottom',
         color="#003366",
         alpha=1.0, 
         backgroundcolor="white" 
         )   
#    graph2 = plot(x_bg, y_bg, "ro", color="#006600", label="IC50 -BG")
    x_bg_range_solid = linspace(X_BG[-1], X_BG[0], 100)
    errorbar(CX_BG, ALL_y_bg, yerr=None, fmt='o', color="lightgreen", label=None)
    errorbar(x_bg, y_bg, yerr=Y_BGerr, fmt='o', color="#006600", label=None)
    graph2_solid = plot(x_bg_range_solid, fitfunc(p1_bg, x_bg_range_solid), "-", color="#006600", label=None)
    graph2_dotted = plot(x_range, fitfunc(p1_bg, x_range), "--", color="#006600", label=None)
    
    # Legend the plot
    xlabel(r"conc [log($\mu$M)]")
    ylabel("inhibition [%]")
    from matplotlib.lines import Line2D
    line = Line2D(range(10), range(10), linestyle='-', marker='o', color="#003366")
    line2 = Line2D(range(10), range(10), linestyle='-', marker='o', color="#006600")
    line3 = Line2D(range(10), range(10), linestyle='-', marker='.', color="gray")
    leg = legend((line, line2, line3, ), ('IC50', 'IC50 -BG', 'BG', ), loc=1)
    ltext  = leg.get_texts()
    setp(ltext, fontsize='small')
    
    res_bg = p1_bg[:]
    log_ic50_bg = res_bg[0]
    res_bg[0] = 10**p1_bg[0]
    ki_bg = (test.lb*res_bg[0]*test.kd)/((test.lt*test.rt)+test.lb*(test.rt-test.lt+test.lb-test.kd))
#    if out_of_scale_BG:
#        if res_bg[0]>9999.0:
#            msg_BG = 'IC50: >9999.0\nR2: {: 7.3f}'.format(Rsquared_BG)
#        else:
#            msg_BG = 'IC50: {: 7.3f}\nR2: {: 7.3f}'.format(res_bg[0], Rsquared_BG)
#    else:
#    if res_bg[0]>9999.0:
#        msg_BG = 'Ki: >999.0\nIC50: >9999.0\nHS:      \nR2: {: 10.3f}'.format(Rsquared_BG)
#    else:
#        msg_BG = 'Ki: {: 10.3f}\nIC50: {: 10.3f}\nHS:      -1.0\nR2:      {: 10.3f}'.format(ki_bg, res_bg[0], Rsquared_BG)
#        
    if res_bg[0]>9999.0:
        msg_BG = 'Ki:   >999.0\nIC50: >9999.0\nHS:       -1.0\nR2:     {: 7.3f}'.format(Rsquared_BG)
    else:
        msg_BG = 'Ki:      {: 7.3f}\nIC50: {: 7.3f}\nHS:       -1.0\nR2:     {: 7.3f}'.format(ki_bg, res_bg[0], Rsquared_BG)
    text(lo+.05, 2,
         msg_BG,
         fontsize=10,
         verticalalignment='bottom',
         color="#006600",
         alpha=1.0, 
         backgroundcolor="white" 
         )
    grid()
    ax = gca()
    ax.set_ylim(-20,120) #  
    ax.set_xlim(lo,hi) #  
    axvline(x=0, color="#2e7682")
    axhline(y=0, color="#2e7682")
    for item in ([ax.xaxis.label, ax.yaxis.label] +ax.get_xticklabels() + ax.get_yticklabels()):
        item.set_fontsize(10)
    if dpi:
        savefig(filepath, dpi=dpi)
    else:
        savefig(filepath)
        savefig(thumbpath, dpi=50)
    close()

    return((round(res[0], 4), round(Rsquared, 4), round(ki, 4)), (round(res_bg[0], 4), round(Rsquared_BG, 4), round(ki_bg, 4)), fluorescence)

#def save_data(X, Y, filepath):
#    from pylab import plot, title, xlabel, ylabel, legend, axes, text, show, savefig
#    from scipy import optimize, linspace
#    x =  X
#    y = Y
#    
#    p0 = [100.0, 0., 0.1,-1.]
#    
#    fitfunc = lambda p,X : p[1] + (p[0]-p[1])/ (1+10**((p[2]-X)*p[3]))
#    errfunc = lambda p, x, y: fitfunc(p, x) - y # Distance to the target function
#    
#    p1, success = optimize.leastsq(errfunc, p0[:], args=(x, y))
#    
#    print p1, success
#    
#    x_range = linspace(-2, 4,100)
#    
#    plot(x, y, "ro", x_range, fitfunc(p1, x_range), "r-", 
#    #x_range, fitfunc(p0, x_range), "b-"
#    ) # Plot of the data and the fit
#    
#    # Legend the plot
#    title("IC50")
#    xlabel("conc [log(uM)]")
#    ylabel("inhibition [%]")
#    legend(('points', 'opt', 
#    #'guess'
#    ))
#    
#    ax = axes()
#    res = p1[:]
#    res[2] = 10**p1[2]
#    text(-0.5, 0,
#         'Top:             %.3f \nBottom:       %.3f\nIC50:           %.3f \nHill Slope:    %.3f'% tuple(res),
#         fontsize=12,
#         verticalalignment='bottom',
#         #transform=ax.transAxes
#         )
#    savefig(filepath)
#    return(tuple(res))

def save_fix_data2(CX, CX_BG, Y_ABCD, Y_ABCD_BG, Ycontrol, filepath, scope, scope_BG, f_list, raw, dpi=None):
    from pylab import plot, title, xlabel, ylabel, legend, axes, text, savefig, grid, clf, gca, axvline, axhline, setp, errorbar
    from scipy import optimize, linspace
    from math import fabs
    from numpy import mean
    props = dict(boxstyle='square', facecolor='white')
    X = []
    X_BG = []
    ABCD = []
    ABCD_BG = []
    for el in scope:
        X.append(CX[int(el)-1])
    for el in scope_BG:
        X_BG.append(CX_BG[int(el)-1])
        
    for row in Y_ABCD:
        list =[]
        for el in scope:
            list.append(row[int(el)-1])
        ABCD.append(list)
    for row in Y_ABCD_BG:
        list =[]
        for el in scope_BG:
            list.append(row[int(el)-1])
        ABCD_BG.append(list)
    x = X
    x_bg = X_BG
    nums =  array(ABCD).T
    nums_BG =  array(ABCD_BG).T
    ALL_nums = array(Y_ABCD).T
    ALL_nums_BG = array(Y_ABCD_BG).T
    # STDEV
    Yerr = nums.std(axis=1)
    Y_BGerr = nums_BG.std(axis=1)
    # Means from array
    y = nums.mean(axis=1).tolist()
    print 'y', y
    y_bg = nums_BG.mean(axis=1).tolist()
    print 'y_bg', y_bg
    ALL_y = ALL_nums.mean(axis=1).tolist()
    ALL_y_bg = ALL_nums_BG.mean(axis=1).tolist()
    
    hi = int(round(max(x)+2, 0))
    lo = int(round(min(x), 0))-1
    print "hi: %s ; lo: %s" % (hi, lo)
    p0_gess = CX[int((len(CX)/2)-1)]
    p0 = [p0_gess,-1.]
    Top = 100
    Bottom = 0
    
    out_of_scale = []
    out_of_scale_BG = []
    
    sections = {} # dict of lists of y.index(el) - for ranges(1,7): >90 | 90-75 | 75-50 | 50-25 | 25-10 | <10
    for el in y:
        if el > 120.0:
            out_of_scale.append((X[y.index(el)], round(el, 4)))
            sections.setdefault(6, []).append(y.index(el))
        elif el > 90.0:
            sections.setdefault(6, []).append(y.index(el))
        elif el <= 90.0 and el > 75.0:
            sections.setdefault(5, []).append(y.index(el))
        elif el <= 75.0 and el > 50.0:
            sections.setdefault(4, []).append(y.index(el))
        elif el <= 50.0 and el > 25.0:
            sections.setdefault(3, []).append(y.index(el))
        elif el <= 25.0 and el > 10.0:
            sections.setdefault(2, []).append(y.index(el))
        elif el <= 10.0 and  el >= -20.0:
            sections.setdefault(1, []).append(y.index(el))
        elif  el < -20.0:
            out_of_scale.append((X[y.index(el)], round(el, 4)))
            sections.setdefault(1, []).append(y.index(el))
    sections_BG = {} # dict of lists of y.index(el) - for ranges(1,7): >90 | 90-75 | 75-50 | 50-25 | 25-10 | <10
    for el in y_bg:
        if el > 120.0:
            out_of_scale_BG.append((X_BG[y_bg.index(el)], round(el, 4)))
            sections_BG.setdefault(6, []).append(y_bg.index(el))
        elif el > 90.0:
            sections_BG.setdefault(6, []).append(y_bg.index(el))
        elif el <= 90.0 and el > 75.0:
            sections_BG.setdefault(5, []).append(y_bg.index(el))
        elif el <= 75.0 and el > 50.0:
            sections_BG.setdefault(4, []).append(y_bg.index(el))
        elif el <= 50.0 and el > 25.0:
            sections_BG.setdefault(3, []).append(y_bg.index(el))
        elif el <= 25.0 and el > 10.0:
            sections_BG.setdefault(2, []).append(y_bg.index(el))
        elif el <= 10.0 and  el >= -20.0:
            sections_BG.setdefault(1, []).append(y_bg.index(el))
        elif  el < -20.0:
            out_of_scale_BG.append((X_BG[y_bg.index(el)], round(el, 4)))
            sections_BG.setdefault(1, []).append(y_bg.index(el))
    for el in y_bg:
        if el > 120.0 or el < -20.0:
            out_of_scale_BG.append((X_BG[y_bg.index(el)], round(el, 4)))
            
    keys = []
    fluorescence = 0
    if raw:
        selected_section = sections
    else:
        selected_section = sections_BG
    for k, v in selected_section.iteritems():
        if len(v)>0:
            keys.append(k)
    k_min = min(keys)
    k_max = max(keys)
    fluorescence += k_max-k_min
    for k, v in selected_section.iteritems():
        if len(v)>0:
            test_me = True
            for vx in v:
                if f_list[vx] == 0:
                    test_me = False
            if test_me:
                fluorescence+=1
        else:
            if k<k_max and k>k_min:
                fluorescence+=1
    
    fitfunc = lambda p,X : Bottom + (Top-Bottom)/ (1+10**((p[0]-X)*p[1]))
    errfunc = lambda p, x, y: fitfunc(p, x) - y # Distance to the target function
    p1,cov,infodict,mesg,ier = optimize.leastsq(errfunc, p0[:], args=(x, y), full_output=True)
    print "p1", p1
    print "cov", cov
    print "infodict", infodict
    print "mesg", mesg
    print "ier", ier
    ss_err=(infodict['fvec']**2).sum()
    ss_tot=((y-mean(y))**2).sum()
    Rsquared=1-(ss_err/ss_tot)
    print "x_bg", x_bg
    print "y_bg", y_bg
    p1_bg ,cov_bg,infodict_bg,mesg_bg,ier_bg = optimize.leastsq(errfunc, p0[:], args=(x_bg, y_bg), full_output=True)
    print "p1_bg", p1_bg
    print "cov_bg", cov_bg
    print "infodict_bg", infodict_bg
    print "ier_bg", ier_bg
    ss_err_bg=(infodict_bg['fvec']**2).sum()
    ss_tot_bg=((y_bg-mean(y_bg))**2).sum()
    Rsquared_BG=1-(ss_err_bg/ss_tot_bg)
    
    x_range = linspace(hi, lo, 100)
    x_range_solid = linspace(X[-1], X[0], 100)
    graph1 = plot(Ycontrol[0], Ycontrol[1], "--", color="gray", label=None)
    errorbar(CX, ALL_y, yerr=None, fmt="o", color="lightblue", label=None)
    errorbar(x, y, yerr=Yerr, fmt="o", color="#003366", label=None)
    graph_solid= plot(x_range_solid, fitfunc(p1, x_range_solid), "-", color="#003366", label=None)
    graph_dotted= plot(x_range, fitfunc(p1, x_range), "--", color="#003366", label=None)
    title("Receptor binding - Fit logIC50")
    ylabel("inhibition [%]")
    res = p1[:]
    log_ic50 = res[0]
    res[0] = 10**p1[0]
#    ki = (test.lb*res[0]*test.kd)/((test.lt*test.rt)+test.lb*(test.rt-test.lt+test.lb-test.kd))
#    if out_of_scale:
#        if res[0]>9999.0:
#            msg = 'IC50: >9999.0\nHS:      {: 7.3f}\noff-scale(x,y): {:}'.format(res[1], out_of_scale)
#        else:
#            msg = 'IC50: {: 7.3f}\nHS:      {: 7.3f}\noff-scale(x,y): {:}'.format(res[0], res[1], out_of_scale)
#    else:
#        if res[0]>9999.0:
#            msg = 'IC50: >9999.0\nHS:      {: 7.3f}'.format(res[1])
#        else:
#            msg = 'IC50: {: 7.3f}\nHS:      {: 7.3f}'.format(res[0], res[1])
    if res[0]>9999.0:
        msg = 'Ki:   >999.0\nIC50: >9999.0\nHS:      {: 7.3f}\nR2:      {: 7.3f}'.format(res[1], Rsquared)
    else:
        msg = 'IC50: {: 7.3f}\nHS:      {: 7.3f}\nR2:      {: 7.3f}'.format(res[0], res[1], Rsquared)
    text(lo+.05, 24,
         msg,
         fontsize=10,
         verticalalignment='bottom',
         color="#003366",
         alpha=1.0, 
         backgroundcolor="white" 
         )   
#    graph2 = plot(x_bg, y_bg, "ro", color="#006600", label="IC50 -BG")
    x_bg_range_solid = linspace(X_BG[-1], X_BG[0], 100)
    errorbar(CX_BG, ALL_y_bg, yerr=None, fmt='o', color="lightgreen", label=None)
    errorbar(x_bg, y_bg, yerr=Y_BGerr, fmt='o', color="#006600", label=None)
    graph2_solid = plot(x_bg_range_solid, fitfunc(p1_bg, x_bg_range_solid), "-", color="#006600", label=None)
    graph2_dotted = plot(x_range, fitfunc(p1_bg, x_range), "--", color="#006600", label=None)
    
    # Legend of the plot
    xlabel(r"conc [log($\mu$M)]")
    ylabel("inhibition [%]")
    from matplotlib.lines import Line2D
    line = Line2D(range(10), range(10), linestyle='-', marker='o', color="#003366")
    line2 = Line2D(range(10), range(10), linestyle='-', marker='o', color="#006600")
    line3 = Line2D(range(10), range(10), linestyle='-', marker='.', color="gray")
    leg = legend((line, line2, line3, ), ('IC50', 'IC50 -BG', 'BG', ), loc=1)
    ltext  = leg.get_texts()
    setp(ltext, fontsize='small')
    
    res_bg = p1_bg[:]
    log_ic50_bg = res_bg[0]
    res_bg[0] = 10**p1_bg[0]
#    ki_bg = (test.lb*res_bg[0]*test.kd)/((test.lt*test.rt)+test.lb*(test.rt-test.lt+test.lb-test.kd))
#    if out_of_scale_BG:
#        if res_bg[0]>9999.0:
#            msg_BG = 'IC50: >9999.0\nHS:      {: 7.3f}\noff-scale(x,y): {:}'.format(res_bg[1], out_of_scale_BG)
#        else:
#            msg_BG = 'IC50: {: 7.3f}\nHS:      {: 7.3f}\noff-scale(x,y): {:}'.format(res_bg[0], res_bg[1], out_of_scale_BG)
#    else:
#        if res_bg[0]>9999.0:
#            msg_BG = 'IC50: >9999.0\nHS:      {: 7.3f}'.format(res_bg[1])
#        else:
#            msg_BG = 'IC50: {: 7.3f}\nHS:      {: 7.3f}'.format(res_bg[0], res_bg[1])
    if res_bg[0]>9999.0:
        msg_BG = 'Ki:   >999.0\nIC50: >9999.0\nHS:      {: 7.3f}\nR2:      {: 7.3f}'.format(res_bg[1], Rsquared_BG)
    else:
        msg_BG = 'IC50: {: 7.3f}\nHS:      {: 7.3f}\nR2:      {: 7.3f}'.format(res_bg[0], res_bg[1], Rsquared_BG)
    text(lo+.5, 2,
         msg_BG,
         fontsize=10,
         verticalalignment='bottom',
         color="#006600",
         alpha=1.0, 
         backgroundcolor="white" 
         )
    grid()
    ax = gca()
    ax.set_ylim(-20,220) #  
    ax.set_xlim(lo,hi) #  
    axvline(x=0, color="#2e7682")
    axhline(y=0, color="#2e7682")
    for item in ([ax.xaxis.label, ax.yaxis.label] +ax.get_xticklabels() + ax.get_yticklabels()):
        item.set_fontsize(10)
    if dpi:
        savefig(filepath, dpi=dpi)
    else:
        savefig(filepath)
    clf()

    return((round(res[0], 4), round(res[1], 4), round(Rsquared, 4)), (round(res_bg[0], 4), round(res_bg[1], 4), round(Rsquared_BG, 4)), fluorescence)

def main():
#    f_path = '/home/adrian/Downloads/962_dominika.ujazdowska_602_p3.xlsx'
    f_path = '/home/adrian/Downloads/960_dominika.ujazdowska_601_p2.xlsx'
#    f_path = '/home/adrian/Downloads/964_dominika.ujazdowska_604_p4.xlsx'
    #concs = [400.0, 200.0, 100.0, 50.0, 25.0, 12.5, 6.25, 3.125, 1.5625, 0.78125]
#    concs = [100.0, 33.333, 11.111, 3.704, 1.235, 0.412, 0.137, 0.046, 0.015, 0.005]
    concs = [1.0, 0.5, 0.25, 0.125, 0.0625, 0.03125, 0.015625, 0.0078125, 0.00390625, 0.00195312]
#    concs = [3.67, 1.835, 0.9175, 0.45875, 0.229375, 0.114688, 0.0573438, 0.0286719, 0.0143359, 0.00716797]

    scope = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
    scope_BG = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
    
    print "print f_path1", f_path
    X, X_BG, Yabcd, Yabcd_BG, Ycontrol, measure_date, temp, fluorescence, top, bottom, f_list = read_topplate(f_path, concs)
    print "print f_path2", f_path
    print "fluorescence", fluorescence
    print 'Y', Yabcd
    print 'Y_BG', Yabcd_BG
    print 'Ycontrol', Ycontrol
    print 'fluorescence', fluorescence
    print 'X', X
    print 'X_BG', X_BG
    print "f_list", f_list
    
    graphs_path = '/home/adrian/test.png'
    
    result_data, result_data_bg, fluorescence = save_fix_data2(X, X_BG, Yabcd, Yabcd_BG, Ycontrol, graphs_path, scope, scope_BG, f_list, raw=False, dpi=None)
    print 'result_data', result_data
    print 'result_data_bg', result_data_bg
    print "fluorescence", fluorescence
    
    
if __name__ == "__main__":
    main()
