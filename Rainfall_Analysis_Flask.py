from flask import Flask, render_template, request

import pandas as pd
import urllib, json #data input from url and reading json
import matplotlib.pyplot as plt # graph plotting
import geopandas as gpd

from bokeh.io import output_notebook, show, output_file, curdoc
from bokeh.plotting import figure
from bokeh.models import GeoJSONDataSource, LinearColorMapper, ColorBar, Div, Panel, HoverTool
from bokeh.palettes import brewer
from bokeh.layouts import widgetbox, row, column
from bokeh.embed import components #To extact scripts & div for Bokeh plot

import folium
from folium import Choropleth, Circle, Marker
from folium.plugins import HeatMap, MarkerCluster

from Rainfall_Analysis_bokeh_sector_admin_weekly import bokeh_plot
#from Rainfall_Analysis_bokeh_sector_admin import bokeh_plot

app = Flask(__name__) #creates a new website in a variable called app


# Index page, no args
@app.route('/') #decorator ties the root URL to the index() function. 
#Therefore, when a user goes the root URL: http://localhost:5000/, the index() function is automatically invoked.
def index_weekly(): 
        
    # Create the Bokeh Plot & Folium and matplotlib
    #plot, folium_html = bokeh_plot()
    plot = bokeh_plot()
    #show(plot)
    # Embed plot into HTML via Flask Render
    script, div = components(plot)
    
    return render_template("index_weekly.html", script=script, div=div)
                           #folium_html=folium_html)

# With debug=True, Flask server will auto-reload 
# when there are code changes
if __name__ == '__main__':
	app.run(port=5000, debug=False) #With debug enabled, Flask will automatically check for code changes and auto-reload these changes. No need to kill Flask and restart it each time you make code changes!