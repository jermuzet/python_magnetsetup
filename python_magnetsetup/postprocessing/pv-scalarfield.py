# trace generated using paraview version 5.9.0
""" 
Console script for paraview.

pvpython pv-temperature.py --cfgfile cfgfile --jsonfile jsonfile --expr heat.example --exprlegend 'T [K]'
"""

import os
import sys

import argparse
from argparse import RawTextHelpFormatter

import re
import json

import argparse

epilog = "The choice of exprs is actually linked with the choosen method following this table\n"

# Manage Options
command_line = None
parser = argparse.ArgumentParser(formatter_class=RawTextHelpFormatter,
                                 description="Post-process for Feelpp/HiFiMagnet simu",
                                 epilog=epilog)


parser.add_argument("--cfgfile", help="input cfg file", default=None)
parser.add_argument("--jsonfile", help="input json file", default=None)
parser.add_argument("--expr", help="set expr to display", type=str, default="heat.temperature")
parser.add_argument("--exprlegend", help="set expr legend to display", type=str, default="T [K]")
parser.add_argument("--resultdir", help="set result directory (default is empty, would get resultdir from cfgfile)", type=str, default="")
parser.add_argument("--wd", help="set a working directory (default is $PWD)", type=str, default="")
args = parser.parse_args()

print(f'args.cfgfile={args.cfgfile}')

# Get current dir
cwd = os.getcwd()
if args.wd:
    os.chdir(args.wd)


#### import the simple module from the paraview
from paraview.simple import *
#### disable automatic camera reset on 'Show'
paraview.simple._DisableFirstRenderCameraReset()

# directory: read cfg, directory=name
with open(args.cfgfile, 'r') as f:
    directory = re.sub('directory=', '', f.readline(),  flags=re.DOTALL)

# get method/time/geom from directory
print(f'directory={directory}')
method_params = directory.split("/")[0].split('-')
print(f'method_params={method_params}')


if not args.resultdir:
    # result dir: feelppdb/{directory}/np_{np}/cfpdes.exports
    results_dir = f'feelppdb/{directory}/np_{args.np}'
else:
    results_dir = args.resultdir

# create a new 'EnSight Reader'
exportcase = EnSightReader(registrationName='Export.case', CaseFileName=f'{results_dir}/{method_params[0]}.exports/Export.case')

# in json exports
# fields: cfpdes.name_field
# other dict entries: cfpdes.expr.name
with open(args.jsonfile) as f:
    data = json.loads(f.read())

postdata = data['PostProcess'][method_params[0]]['Exports']

pfields = {}
for expr in postdata['expr']:
    print(f'expr={expr} ({type(expr)})')
    pfields[expr] = [f'{method_params[0]}.expr.{expr}', f'{method_params[0]}expr{expr}']
print(f'pfiels: {pfields}')

for field in postdata['fields']:
    print(f'field={field}, type={type(field)}')
    pfields[field] = [ f'{method_params[0]}.{field}', f'{method_params[0]}{field.replace(".","")}']
print(f'pfiels: {pfields}')

exportcase.PointArrays = [ pfields[key][0] for key in sorted(pfields.keys()) ]
expr0 = sorted(pfields.keys())[0]
print(f'1st expr: {expr0} --> {pfields[expr0][1]}')

if not args.expr in pfields:
    print(f'{args.expr} is not a valid field')
    print(f'valid values are:',[expr for key in pfields])
    sys.exit(1)

print(f'Display {pfields[args.expr][0]}')

# get active view
renderView1 = GetActiveViewOrCreate('RenderView')

# show data in view
exportcaseDisplay = Show(exportcase, renderView1, 'UnstructuredGridRepresentation')

# get color transfer function/color map for 'cfpdesexprJth'
cfpdesexprJthLUT = GetColorTransferFunction(pfields[expr0][1])

# get opacity transfer function/opacity map for 'cfpdesexprJth'
cfpdesexprJthPWF = GetOpacityTransferFunction(pfields[expr0][1])

# trace defaults for the display properties.
exportcaseDisplay.Representation = 'Surface'
exportcaseDisplay.ColorArrayName = ['POINTS', pfields[expr0][0]] #'cfpdes.expr.Jth']
exportcaseDisplay.LookupTable = cfpdesexprJthLUT
exportcaseDisplay.SelectTCoordArray = 'None'
exportcaseDisplay.SelectNormalArray = 'None'
exportcaseDisplay.SelectTangentArray = 'None'
exportcaseDisplay.OSPRayScaleArray = pfields[expr0][0] #'cfpdes.expr.Jth'
exportcaseDisplay.OSPRayScaleFunction = 'PiecewiseFunction'
exportcaseDisplay.SelectOrientationVectors = 'None'
exportcaseDisplay.ScaleFactor = 0.035400000214576725
exportcaseDisplay.SelectScaleArray = pfields[expr0][0] #'cfpdes.expr.Jth'
exportcaseDisplay.GlyphType = 'Arrow'
exportcaseDisplay.GlyphTableIndexArray = pfields[expr0][0] # 'cfpdes.expr.Jth'
exportcaseDisplay.GaussianRadius = 0.001770000010728836
exportcaseDisplay.SetScaleArray = ['POINTS', pfields[expr0][0]] # 'cfpdes.expr.Jth']
exportcaseDisplay.ScaleTransferFunction = 'PiecewiseFunction'
exportcaseDisplay.OpacityArray = ['POINTS', pfields[expr0][0]] #'cfpdes.expr.Jth']
exportcaseDisplay.OpacityTransferFunction = 'PiecewiseFunction'
exportcaseDisplay.DataAxesGrid = 'GridAxesRepresentation'
exportcaseDisplay.PolarAxes = 'PolarAxesRepresentation'
exportcaseDisplay.ScalarOpacityFunction = cfpdesexprJthPWF
exportcaseDisplay.ScalarOpacityUnitDistance = 0.017126900091946815
exportcaseDisplay.OpacityArrayName = ['POINTS', pfields[expr][0]] #'cfpdes.expr.Jth']
exportcaseDisplay.ExtractedBlockIndex = 1

# init the 'PiecewiseFunction' selected for 'ScaleTransferFunction'
exportcaseDisplay.ScaleTransferFunction.Points = [-393612608.0, 0.0, 0.5, 0.0, 0.0, 1.0, 0.5, 0.0]

# init the 'PiecewiseFunction' selected for 'OpacityTransferFunction'
exportcaseDisplay.OpacityTransferFunction.Points = [-393612608.0, 0.0, 0.5, 0.0, 0.0, 1.0, 0.5, 0.0]

# reset view to fit data
renderView1.ResetCamera()

#changing interaction mode based on data extents
renderView1.InteractionMode = '2D'
renderView1.CameraPosition = [0.02500000037252903, -0.04899999499320984, 10000.0]
renderView1.CameraFocalPoint = [0.02500000037252903, -0.04899999499320984, 0.0]

# show color bar/color legend
exportcaseDisplay.SetScalarBarVisibility(renderView1, True)

# update the view to ensure updated data information
renderView1.Update()

# set scalar coloring
ColorBy(exportcaseDisplay, ('POINTS', pfields[args.expr][0]))

# Hide the scalar bar for this color map if no visible data is colored by it.
HideScalarBarIfNotNeeded(cfpdesexprJthLUT, renderView1)

# rescale color and/or opacity maps used to include current data range
exportcaseDisplay.RescaleTransferFunctionToDataRange(True, False)

# show color bar/color legend
exportcaseDisplay.SetScalarBarVisibility(renderView1, True)

# get color transfer function/color map for 'cfpdesheattemperature'
print(f'cfpdesheattemperatureLUT = GetColorTransferFunction({pfields[args.expr][1]})')
cfpdesheattemperatureLUT = GetColorTransferFunction(pfields[args.expr][1])

# get opacity transfer function/opacity map for 'cfpdesheattemperature'
cfpdesheattemperaturePWF = GetOpacityTransferFunction(pfields[args.expr][1])

# get color legend/bar for cfpdesheattemperatureLUT in view renderView1
cfpdesheattemperatureLUTColorBar = GetScalarBar(cfpdesheattemperatureLUT, renderView1)

# Properties modified on cfpdesheattemperatureLUTColorBar
cfpdesheattemperatureLUTColorBar.WindowLocation = 'UpperRightCorner'
cfpdesheattemperatureLUTColorBar.Title = args.exprlegend # TODO custom 
cfpdesheattemperatureLUTColorBar.TitleFontSize = 24

#================================================================
# addendum: following script captures some of the application
# state to faithfully reproduce the visualization during playback
#================================================================

# get layout
layout1 = GetLayout()

#--------------------------------
# saving layout sizes for layouts

# layout/tab size in pixels
layout1.SetSize(2495, 1864)

#-----------------------------------
# saving camera placements for views

# current camera placement for renderView1
renderView1.InteractionMode = '2D'
renderView1.CameraPosition = [0.02500000037252903, -0.04899999499320984, 10000.0]
renderView1.CameraFocalPoint = [0.02500000037252903, -0.04899999499320984, 0.0]
renderView1.CameraParallelScale = 0.17709175693856544

#--------------------------------------------
# uncomment the following to render all views
# RenderAllViews()
# alternatively, if you want to write images, you can use SaveScreenshot(...).# save screenshot

# export file to proper directory??
imagefile = f'{args.expr}.png'
SaveScreenshot(imagefile, renderView1, ImageResolution=[888, 835])
