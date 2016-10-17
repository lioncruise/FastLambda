#! /usr/bin/env python

from zplot import *

# populate zplot table from data file
t = table('bin/forks.data')

# create the postscript file we'll use as our canvas
canvas = postscript('imgs/forks.eps')

# on the x-axis, we want categories, not numbers.  Thus, we
# determine the number of categories by checking the max
# "rownumber" (a field automatically added by zplot).  We want a
# half bar width (0.5) to the left and right of the bar locations
# so we don't overflow the drawable.
d = drawable(canvas, xrange=[-0.5,t.getmax('rownumber')+0.5], yrange=[0,10])

# xmanual is a list of the form [(label1,x1), (label2,x2), ...].
# We want to use the "op" field from the data file as our labels
# and use "rownumber" as our x coordinate.
axis(d, xtitle='Year', xmanual=t.query(select='year,rownumber'),
     ytitle='Avg. Forks', yauto=[0,10,2], xlabelrotate=45, xlabelfontsize=6.5)

# we are going to create several bars with similar arguments.  One
# easy way to do this is to put all the arguments in a dict, and
# use Python's special syntax ("**") for using the dict as named
# args.  Then we can tweak the args between each call to
# verticalbars.
#
# yfield determines the bar height, and stackfields determines
# where the bottom of a bar starts.  This is useful for showing
# several bar sections to indicate a breakdown.  After the first
# bar, we append the previous yfield to stackfields to stack the bars.
p = plotter()

barargs = {'drawable':d, 'table':t, 'xfield':'rownumber',
           'linewidth':0, 'fill':True, 'barwidth':0.8,
           'stackfields':[]}

pointargs = {'drawable':d, 'table':t, 'xfield':'rownumber',
           'linewidth':1.2, 'style':'hline', 'yfield':'median',
           'linecolor':'black', 'size':6.5} 

barargs['yfield'] = 'mean'
barargs['fillcolor'] = 'orange'
p.verticalbars(**barargs)
p.points(**pointargs)
 
canvas.render()
