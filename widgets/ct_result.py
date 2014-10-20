# -*- coding: utf-8 -*-
import xlrd
import os
from datetime import datetime
from numpy import array, matrix

def save_fix_data(X, Y, filepath, dpi=None):
    from pylab import plot, title, xlabel, ylabel, legend, axes, text, savefig, grid, clf, gca, axvline, axhline, setp, errorbar, close
    from scipy import optimize, linspace
    from math import fabs
    from numpy import mean
    
    #create thumb file name:
    head, tail = os.path.split(filepath)        
    thumbpath = os.path.join(head, "thumb_"+tail)
    
    
    props = dict(boxstyle='square', facecolor='white')
    x = X
    nums =  array(Y).T
    # STDEV
    Yerr = nums.std(axis=1)
    y = list(nums.mean(axis=1))
    hi = max(x)+1.0
    lo = min(x)-.5
    p0_gess = X[int((len(X)/2)-1)]
    p0 = [p0_gess,-1.]
    Top = 100
    Bottom = 0
    
    out_of_scale = []
    for el in y:
        if el > 120.0 or el < -20.0:
            out_of_scale.append((X[y.index(el)], round(el, 3)))
    
    fitfunc = lambda p,X : Bottom + (Top-Bottom)/ (1+10**((p[0]-X)*p[1]))
    errfunc = lambda p, x, y: fitfunc(p, x) - y # Distance to the target function
    p1,cov,infodict,mesg,ier = optimize.leastsq(errfunc, p0[:], args=(x, y), full_output=True)
    ss_err=(infodict['fvec']**2).sum()
    ss_tot=((y-mean(y))**2).sum()
    Rsquared=1-(ss_err/ss_tot)

    
    x_range = linspace(hi, lo, 100)
    x_range_solid = linspace(X[-1], X[0], 100)
    errorbar(x, y, yerr=Yerr, fmt="o-", color="#003366", label=None)
#    graph_solid= plot(x_range_solid, fitfunc(p1, x_range_solid), "-", color="green", label=None)
    graph_dotted= plot(x_range, fitfunc(p1, x_range), "--", color="gray", label=None)
    title("IC50")
    ylabel("Cell Viability [%]")
    res = p1[:]
    log_ic50 = res[0]
    res[0] = 10**p1[0]
    if res[0]>9999.0:
        msg = '\nIC50: >9999.0\nHS:      {: 7.2f}\nR2:      {: 7.2f}'.format(res[1], Rsquared)
    else:
        msg = '\nIC50: {: 7.2f}\nHS:      {: 7.2f}\nR2:      {: 7.2f}'.format(res[0], res[1], Rsquared)
    text(lo+0.1, -18,
         msg,
         fontsize=9,
         verticalalignment='bottom',
         color="#003366",
         alpha=1.0, 
         backgroundcolor="white" 
         )   
#    graph2 = plot(x_bg, y_bg, "ro", color="#006600", label="IC50 -BG")

    # Legend the plot
    xlabel(r"conc [log($\mu$M)]")
    ylabel("Cell Viability [%]")
    from matplotlib.lines import Line2D
    line = Line2D(range(10), range(10), linestyle='-', marker='o', color="#003366")
    leg = legend((line, ), ('IC50', ), loc=1)
    ltext  = leg.get_texts()
    setp(ltext, fontsize='small')
    
    grid()
    ax = gca()
    ax.set_ylim(-20,120) #  
    ax.set_xlim(lo, hi) #  
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

    return((round(res[0], 3), round(res[1], 3), round(Rsquared, 3)))
    
def save_data_fix_HS(X, Y, filepath, dpi=None):
    from pylab import plot, title, xlabel, ylabel, legend, axes, text, savefig, grid, clf, gca, axvline, axhline, setp, errorbar, close
    from scipy import optimize, linspace
    from math import fabs
    from numpy import mean
    
    #create thumb file name:
    head, tail = os.path.split(filepath)        
    thumbpath = os.path.join(head, "thumb_"+tail)    
    
    props = dict(boxstyle='square', facecolor='white')
    x = X
    nums =  array(Y).T
    Yerr = nums.std(axis=1)     # STDEV
    y = list(nums.mean(axis=1)) # mean
    hi = max(x)+1.0
    lo = min(x)-.5
    p0_gess = X[int((len(X)/2)-1)]
    p0 = [p0_gess]
    Top = 100
    Bottom = 0
    
    out_of_scale = []
    for el in y:
        if el > 120.0 or el < -20.0:
            out_of_scale.append((X[y.index(el)], round(el, 3)))
    
    fitfunc = lambda p,X : Bottom + (Top-Bottom)/ (1+10**((p[0]-X)*(-1.)))
    errfunc = lambda p, x, y: fitfunc(p, x) - y # Distance to the target function
    p1,cov,infodict,mesg,ier = optimize.leastsq(errfunc, p0[:], args=(x, y), full_output=True)
    ss_err=(infodict['fvec']**2).sum()
    ss_tot=((y-mean(y))**2).sum()
    Rsquared=1-(ss_err/ss_tot)

    
    x_range = linspace(hi, lo, 100)
    x_range_solid = linspace(X[-1], X[0], 100)
    errorbar(x, y, yerr=Yerr, fmt="o-", color="#003366", label=None)
#    graph_solid= plot(x_range_solid, fitfunc(p1, x_range_solid), "-", color="green", label=None)
    graph_dotted= plot(x_range, fitfunc(p1, x_range), "--", color="gray", label=None)
    title("IC50")
    ylabel("Cell Viability [%]")
    res = p1[:]
    log_ic50 = res[0]
    res[0] = 10**p1[0]
    if res[0]>9999.0:
        msg = 'IC50: >9999.0\nHS:      {: 7.2f}\nR2:      {: 7.2f}'.format(res[1], Rsquared)
    else:
        msg = 'IC50: {: 7.2f}\nHS:      {: 7.2f}\nR2:      {: 7.2f}'.format(res[0], -1.0, Rsquared)
    text(lo+0.1, 24,
         msg,
         fontsize=10,
         verticalalignment='bottom',
         color="#003366",
         alpha=1.0, 
         backgroundcolor="white" 
         )   
#    graph2 = plot(x_bg, y_bg, "ro", color="#006600", label="IC50 -BG")

    # Legend the plot
    xlabel(r"conc [log($\mu$M)]")
    ylabel("Cell Viability [%]")
    from matplotlib.lines import Line2D
    line = Line2D(range(10), range(10), linestyle='-', marker='o', color="#003366")
    leg = legend((line, ), ('IC50', ), loc=1)
    ltext  = leg.get_texts()
    setp(ltext, fontsize='small')
    
    grid()
    ax = gca()
    ax.set_ylim(-20,120) #  
    ax.set_xlim(lo, hi) #  
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

    return((round(res[0], 3), round(Rsquared, 3)))

def multigraph(CONCS, DATAS, NAMES, filepath, dpi=None):
    from pylab import plot, title, xlabel, ylabel, legend, axes, text, savefig, grid, clf, gca, axvline, axhline, setp, errorbar, close
    from scipy import optimize, linspace
    from math import fabs
    from numpy import mean
    from matplotlib import cm
    from matplotlib.lines import Line2D
    hi = 0
    lo = 10
    p0 = [1,-1.]
    Top = 100
    Bottom = 0
    NUM_COLORS = len(DATAS)
    cmx = cm.get_cmap('Dark2')
    colors_map = ['blue', 'green', 'red', 'orange', '#8A2BE2', 'black', '#00FFFF', 'lime', 'brown','gold','magenta', 'gray', '#1E90FF', '#808000', '#FF6347', '#DAA520', 'pink', 'tan']
    LINES = ()
    for i in range(len(DATAS)):
        X = CONCS[i]
        x=X
        Y = DATAS[i]
        nums =  array(Y).T
        Yerr = nums.std(axis=1)
        y = list(nums.mean(axis=1))
        if hi < max(x)+.1:
            hi = max(x)+.1
        if lo > min(x)-.1:
            lo = min(x)-.1
        
        fitfunc = lambda p,X : Bottom + (Top-Bottom)/ (1+10**((p[0]-X)*p[1]))
        errfunc = lambda p, x, y: fitfunc(p, x) - y # Distance to the target function
        p1,cov,infodict,mesg,ier = optimize.leastsq(errfunc, p0[:], args=(x, y), full_output=True)
#        ss_err=(infodict['fvec']**2).sum()
#        ss_tot=((y-mean(y))**2).sum()
#        Rsquared=1-(ss_err/ss_tot)
#    
        
        x_range = linspace(hi, lo, 100)
        x_range_solid = linspace(X[-1], X[0], 100)
        try:
            colorVal = colors_map[i]
        except Exception:
            colorVal = cmx(1.*i/NUM_COLORS)
        errorbar(x, y, yerr=Yerr, fmt="o-", color=colorVal, label=None)
        line = Line2D(range(10), range(10), linestyle='-', marker='o', color=colorVal)
        LINES += (line, )
        i+=1
    #    graph_solid= plot(x_range_solid, fitfunc(p1, x_range_solid), "-", color="green", label=None)
#        graph_dotted= plot(x_range, fitfunc(p1, x_range), "--", color="gray", label=None)
    grid()
    ax = gca()
    ax.set_ylim(-20,140) #  
    ax.set_xlim(lo, hi) #  
    axvline(x=0, color="#2e7682")
    axhline(y=0, color="#2e7682")
    leg = legend(LINES, NAMES, loc=1, bbox_to_anchor=(1.45, 1.02))
#    leg = legend(LINES, NAMES, loc=3)
    ltext  = leg.get_texts()
    setp(ltext, fontsize='small')
    title("IC50")
    ylabel("Cell Viability [%]")
    if dpi:
        savefig(filepath, bbox_extra_artists=(leg,), bbox_inches='tight', dpi=dpi)
    else:
        savefig(filepath, bbox_extra_artists=(leg,), bbox_inches='tight')
    close()

def read_many(filepath):
    import csv
    assert os.path.splitext(filepath)[1] == '.csv', u'Nieprawidłowe rozszerzenie pliku. Wymagane rozszerzenie: "csv"'
    concs = []
    macierz = []
    with open(filepath, 'rb') as csvfile:
        spamreader = csv.reader(csvfile, delimiter=';', quotechar='"')
        for row in spamreader:
            from math import log10
            if row[0] != '':
                try:
                    conc = float(row[0].replace(',', '.'))
                except Exception:
                    conc = 0.0
                if conc >0.0:
                    concs.append(round(log10(conc), 3))
            list = []
            for el in row[1:]:
                if el != '':
                    list.append(el)
            macierz.append(list)
    M = matrix(macierz)
    M = M.transpose()
    M = M.tolist()
    return(concs, M) #zakomentuj 
    
def read_one(filepath):
    import csv
    assert os.path.splitext(filepath)[1] == '.csv', u'Nieprawidłowe rozszerzenie pliku. Wymagane rozszerzenie: "csv"'
    concs = []
    macierz = []
    with open(filepath, 'rb') as csvfile:
        spamreader = csv.reader(csvfile, delimiter=';', quotechar='"')
        for row in spamreader:
            if row[0] != '':
                try:
                    conc = float(row[0].replace(',', '.'))
                except Exception:
                    conc = 0.0
                if conc !=0.0:
                    conc = float(row[0].replace(',', '.'))
                    concs.append(round(conc, 3))
            list = []
            for el in row[1:]:
                if el != '':
                    list.append(el)
            macierz.append(list)
    M = matrix(macierz)
    M = M.transpose()
    M = M.tolist()
    return(concs, M)
    
def write_result(top, concs, data, filepath):
    import csv
    with open(filepath, 'wb') as csvfile:
        spamwriter = csv.writer(csvfile, delimiter=';', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        first_line = [0] +top
        spamwriter.writerow(first_line)
        assert len(data) == 3, u'za mało danych'
        assert len(concs) == len(data[0]), 'liczba stężeń różna od ilości danych'
        i=0
        for el in concs:
            list = [el]
            for row in data:
                try:
                    list.append(row[i])
                except Exception:
                    list.append('*')
            spamwriter.writerow(list)
            i+=1

def main():
    # parse command line options
    import sys
    import getopt
    try:
        opts, args = getopt.getopt(sys.argv[1:], "h", ["help"])
    except getopt.error, msg:
        print msg
        print "for help use --help"
        sys.exit(2)
    # process options
    for o, a in opts:
        if o in ("-h", "--help"):
            print __doc__
            sys.exit(0)
    imgpath = '/home/adrian/test2.png'
    filepath = sys.argv[1]
    X, M = read_many(filepath)
    print 'X', X
    for row in M:
        print M.index(row), row, len(row)
    name, top, data=[None, None, None]
    OO = 0
    for row in M:
        print 'M.index(row)', M.index(row)
        if not (M.index(row) %3):
            OO += 1
            print OO
            if top and data:
                for line in data:
                    for el in line:
                        line[line.index(el)] = 100.0*el/(sum(top)/len(top))
            name = row[0]
            top = [float(row[1].replace(',', ''))]
            list = []
            data =[]
            for el in row[2:]:
                el = float(el.replace(',', ''))
                list.append(round(el, 3))
            data.append(list)
            print 'data', len(data), data
        else:
            assert row[0] == name, u'Zły format pliku'
            top.append(float(row[1].replace(',', '')))
            i=0
            list=[]
            for el in row[2:]:
                el =float(el.replace(',', ''))
                list.append(round(el, 3))
            data.append(list)
            print 'data', len(data), data
    
    
def main_one():
    # parse command line options
    import sys
    import getopt
    try:
        opts, args = getopt.getopt(sys.argv[1:], "h", ["help"])
    except getopt.error, msg:
        print msg
        print "for help use --help"
        sys.exit(2)
    for o, a in opts:
        if o in ("-h", "--help"):
            print __doc__
            sys.exit(0)
    filepath = sys.argv[1]
    X, M = read_one(filepath)
    imgpath = '/home/adrian/test2.png'
    print 'X', X, len(X)
    print 'M', M, len(M[0])
    top=[]
    for row in M:
        print '1', M.index(row) %3, M.index(row)
        print 'row ', row 
        top += [float(row[0].replace(',', '.'))]
        list = []
        data =[]
        for el in row[1:]:
            el = float(el.replace(',', '.'))
            list.append(round(el, 3))
        data.append(list)
    if top and data:
        print 'sum(top)', sum(top), 'len(top)', len(top)
        print 'avg(top)', sum(top)/len(top)
        for line in data:
            for el in line:
                line[line.index(el)] = 100.0*el/(sum(top)/len(top))
        ic50, hillslope, r2 = save_fix_data(X, data, imgpath)
        print "ic50\t", "r2"
        print ic50, "\t", r2
    
if __name__ == "__main__":
#    main()
    main_one()
