#!/usr/bin/env python
# 
"""
These functions, when given a magnitude mag between cmin and cmax, return
a colour tuple (red, green, blue). yellow is cold (low magnitude)
and red is hot (high magnitude).

"""
#import math

def floatRgb(mag, cmin, cmax):
       """
       Return a tuple of floats between 0 and 1 for the red, green and
       blue amplitudes.
       """
       if mag <=1:
           mag = mag *39
       elif mag >1 and mag <=10:
           mag = mag*3 +40
       elif mag >10 and mag <=100:
           mag = mag*3/10 + 70
       elif mag >100:
           mag = 100
       try:
              # normalize to [0,1]
              if cmin <0.0:
                  cmin = 0.0
              x = float(mag-cmin)/float(cmax-cmin)
       except:
              # cmax = cmin
              x = 0.5
       #blue = min((max((4*(0.75-x), 0.)), 1.))
       #red  = min((max((4*(x-0.25), 0.)), 1.))
       #green= min((max((4*math.fabs(x-0.5)-1., 0.)), 1.))
       blue = min((max((0.15-x, 0.0)), 0.85))
       red  = 1.0
       green= min((max(((1.15-x), 0.0)), .85))
       return (red, green, blue)

def strRgb(mag, cmin, cmax):
       """
       Return a tuple of strings to be used in Tk plots.
       """

       red, green, blue = floatRgb(mag, cmin, cmax)       
       return "#%02x%02x%02x" % (red*255, green*255, blue*255)

def rgb(mag, cmin, cmax):
       """
       Return a tuple of integers to be used in AWT/Java plots.
       """

       red, green, blue = floatRgb(mag, cmin, cmax)
       return (int(red*255), int(green*255), int(blue*255))

def htmlRgb2(mag, cmin, cmax):
       """
       Return a tuple of strings to be used in HTML documents.
       """
       return "#%02x%02x%02x"%rgb(mag, cmin, cmax)

def htmlRgb(mag, cmin, cmax):
       """
       Return a tuple of strings to be used in HTML documents.
       """
       return "rgba(%s, %s, %s, 0.8)"%rgb(mag, cmin, cmax)
       
def floatRgb100(mag, cmin, cmax):
       """
       Return a tuple of floats between 0 and 1 for the red, green and
       blue amplitudes.
       """
       if mag >1 and mag <=10:
           mag = mag*3
       elif mag >10 and mag <=50:
           mag = mag*3/10 + 40
       elif mag >10 and mag <=50:
           mag = mag*3/10 + 60
       elif mag >100:
           mag = 100
       try:
              # normalize to [0,1]
              if cmin <0.0:
                  cmin = 0.0
              x = float(mag-cmin)/float(cmax-cmin)
       except:
              # cmax = cmin
              x = 0.5
       blue = min((max((0.15-x, 0.0)), 0.85))
       red  = 1.0
       green= min((max(((1.15-x), 0.0)), .85))
       return (red, green, blue)
       
def rgb100(mag, cmin, cmax):
       """
       Return a tuple of integers to be used in AWT/Java plots.
       """
       red, green, blue = floatRgb100(mag, cmin, cmax)
       return (int(red*255), int(green*255), int(blue*255))
       
def htmlRgb100(mag, cmin, cmax):
       """
       Return a tuple of strings to be used in HTML documents.
       """
       return "rgba(%s, %s, %s, 0.8)"%rgb100(mag, cmin, cmax)
    
def Num2Rgb(x):
       blue = int(min((max((0.15-x, 0.0)), 0.85))*255)
       red  = int(255.0)
       green= int(255-min((max(((1.15-x), 0.0)), .85))*255)
       return "rgba(%s, %s, %s, 0.9)"%(red, green, blue)
       
#-------------------------------------------- RAW ------------------------------------------ #


def getRGB(val, cmin, cmax):
    """
    Return a tuple of floats between 0 and 1 for the red, green and
    blue amplitudes. Colormap: yellow -> red
    """
    if cmin <0.0:
        cmin = 0.0
    if  val > cmax:
        val = cmax
        
    v = val - cmin
    d = (cmax-cmin) * 0.5

    blue = 0.0
    if v<=d:
        red  = (255*v)/d
        green = 255
    else:
        red = 255
        green = 255 - (255 * (v-d))/(cmax-cmin-d)
    return "#%02x%02x%02x"%(red, green, blue)
    
def getRGB(val, cmin, cmax):
    """
    Return a tuple of floats between 0 and 1 for the red, green and
    blue amplitudes. Colormap: green - > yellow -> red
    """
    if cmin <0.0:
        cmin = 0.0
    if  val > cmax:
        val = cmax
        
    v = val - cmin
    d = (cmax-cmin) * 0.5

    blue = 0.0
    if v<=d:
        red  = (255*v)/d
        green = 255
    else:
        red = 255
        green = 255 - (255 * (v-d))/(cmax-cmin-d)
    return "#%02x%02x%02x"%(red, green, blue)

def getRGB2(val, cmin, cmax):
    """
    Return a tuple of floats between 0 and 1 for the red, green and
    blue amplitudes. Colormap: yellow -> red
    source: http://awesome.naquadah.org/wiki/Gradient
    """
    red = 255
    green = 255
    blue = 0
    to_red = 245
    to_green = 80
    to_blue = 80
    
    factor = 0
    if val >= cmax:
        factor = 1
    elif val > cmin:
        factor = (val - cmin)/(cmax - cmin)
    
    red   = red   + (factor * (to_red   - red))
    green = green + (factor * (to_green - green))
    blue  = blue  + (factor * (to_blue  - blue))

    return "#%02x%02x%02x"%(red, green, blue)
    
def getRGB3(color, to_color, val, cmin, cmax):
    """
    Return a tuple of floats between 0 and 1 for the red, green and
    blue amplitudes. Colormap: color tuple -> to_color tuple
    source: http://awesome.naquadah.org/wiki/Gradient
    """
    red, green, blue = color
    to_red, to_green, to_blue = to_color
    
    factor = 0.001
    if val >= cmax:
        factor = 1
    elif val > cmin:
        factor = (val - cmin)/(cmax - cmin)
    
    red   = red   + (factor * (to_red   - red))
    green = green + (factor * (to_green - green))
    blue  = blue  + (factor * (to_blue  - blue))

    return "#%02x%02x%02x"%(red, green, blue)
