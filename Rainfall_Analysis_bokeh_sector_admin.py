import pandas as pd
import urllib, json #data input from url and reading json
import matplotlib.pyplot as plt # graph plotting
import geopandas as gpd
from math import pi
from Rainfall_Analysis_matplotlib import rain_analysis_mat

def bokeh_plot():
    #1: Read shape file as geoDataFrame
    #Pune admin level data - https://github.com/datameet
    fp = 'E:\Coursera Material\Python For Everyone\Birds\Owl analysis\Datameet\Pune_wards-master\GeoData\pune-admin-wards.geojson'
    #reading the file stored in variable fp
    map_df = gpd.read_file(fp)
    map_df.plot(color='skyblue', linewidth=0.1, edgecolor='black')
    
    #2: Read ward to sector data
    rain_data = 'E:\Coursera Material\Python For Everyone\Pune Rainfall\Rainfall Volunteers_2020 daily.xlsx'
    rain_data_spreadsheet = pd.read_excel(rain_data, sheet_name=None)
    
    admin_to_sector = rain_data_spreadsheet['Sector_admin']
    
    map_df_admin = map_df.merge(admin_to_sector, on='name')
    
    map_df_sector = map_df_admin[['geometry','Sector']]
    map_df_sector = map_df_sector.dissolve(by='Sector')
    map_df_sector.reset_index(inplace=True)
    
    #Reference link - https://www.earthdatascience.org/workshops/gis-open-source-python/dissolve-polygons-in-python-geopandas-shapely/
    
    #saving file as geojson format
    map_df_sector.to_file("pune_sectors.geojson", driver='GeoJSON')
    
    
    #3.1: Calculate centroid of a multipolygon
    map_df_sector["centroid"] = map_df_sector["geometry"].centroid
    
    for index, row in map_df_sector.iterrows():
        centroid_coords = row.geometry.centroid.coords.xy
        map_df_sector.loc[index, 'cen_x'] = centroid_coords[0][0]
        map_df_sector.loc[index, 'cen_y'] = centroid_coords[1][0]
    
    map_df_sector.drop(['centroid'], axis=1, inplace=True)
    
    
    #Read data to json.
    merged_json = json.loads(map_df_sector.to_json())
    #Convert to String like object.
    json_data = json.dumps(merged_json)
    
    #json check - merged_json['features'][17]['properties']
    #Plot Bokeh graph
    from bokeh.io import output_notebook, show, output_file, curdoc
    from bokeh.plotting import figure
    from bokeh.models import GeoJSONDataSource, ColumnDataSource, LinearColorMapper, ColorBar, Div, Panel
    from bokeh.models import (Slider,HoverTool,Select, DatetimeTickFormatter, LabelSet)
    from bokeh.palettes import brewer
    from bokeh.layouts import widgetbox, row, column
    from bokeh.transform import factor_cmap
    from bokeh.tile_providers import get_provider, Vendors
    from bokeh.palettes import Spectral6
    
    #Input GeoJSON source that contains features for plotting.
    geosource = GeoJSONDataSource(geojson = json_data)
    
    #Create Pune City map object.
    p = figure(title = 'Rainfall collection points in Pune City', plot_height = 600 , plot_width = 600, 
               toolbar_location = None, match_aspect=True)
    p.xgrid.grid_line_color = None
    p.ygrid.grid_line_color = None
    tile_provider = get_provider(Vendors.OSM)
    p.add_tile(tile_provider) #to investigate why tile is not getting rendered
    #Add patch renderer to figure. 
    p.patches('xs','ys', source = geosource, line_color = 'black', line_width = 0.5, fill_alpha = 0)
    
    #p.add_tools(HoverTool(renderers=[r1], tooltips=[ ('admin name','@name')]))
    
    labels = LabelSet(x='cen_x', y='cen_y', source = geosource, text='Sector', level='glyph',
                      x_offset=0, y_offset=0, render_mode='css')
    p.add_layout(labels)
    
    #Plot rain data collection pointson Pune City map object
    
    rain_data = rain_data_spreadsheet['June_per_day']
    rain_data['Date'] = rain_data['Date'].dt.date
    rain_data_scope = rain_data[(rain_data['Region']=='PMC') &
                                (rain_data['Obs Status']=='complete')]
    
    #Allocate rain_data points to 'Sector'
    
    rain_data_GeoDataFrame = gpd.GeoDataFrame(rain_data_scope, geometry=gpd.points_from_xy(rain_data_scope.Long,
                                                                                           rain_data_scope.Lat))
    rain_data_GeoDataFrame.crs = {'init': 'epsg:4326'}
    rain_data_alloc_to_Sector = gpd.sjoin(rain_data_GeoDataFrame, map_df_sector)
    
    rain_data_total = rain_data_alloc_to_Sector.groupby(['Region','Location','Lat','Long','Obs Status','Sector']).sum()[['Rainfall']].reset_index()
    
    rain_data_total = rain_data_total.sort_values(by=['Sector','Location'])
    rain_data_points = ColumnDataSource(data = {'x': rain_data_total['Long'], 
                                                'y': rain_data_total['Lat'],
                                                'Obs Status': rain_data_total['Obs Status'],
                                                'Location':rain_data_total['Location'],
                                                'Rainfall':rain_data_total['Rainfall']})
    STATUS = ['complete','na']
    STATUS_colour = ['green','orange']
    r2= p.circle('x', 'y', source = rain_data_points, alpha = 0.4, legend_field='Obs Status', 
                  color = factor_cmap('Obs Status', STATUS_colour, STATUS),#'navy',
                  size = 10)
    p.add_tools(HoverTool(renderers=[r2], tooltips=[ ('Location','@Location')]))
    
    
    #Create Bar chart:
    '''
    Method 1:
    b = figure(x_range=rain_data_total['Location'], y_range=(0,200),plot_height=700, title="Sector Wise Rainfall",
               toolbar_location=None, tools="")
    b.vbar(x=rain_data_total['Location'], top=rain_data_total['Rainfall'], width=0.5)
    '''
    
    #Method 2:
    bar_chart_data = ColumnDataSource(data = {'x': rain_data_total['Location'], 
                                              'y': rain_data_total['Rainfall'],
                                              'Sector': rain_data_total['Sector']})
                                              
    sector = rain_data_total['Sector'].unique()
    b = figure(x_range=rain_data_total['Location'], y_range=(0,100),plot_height=400, title="Sector Wise Rainfall",
               toolbar_location=None)
    b.vbar(x='x', top='y', width=0.5, source=bar_chart_data,legend_field='Sector',
           color=factor_cmap('Sector',Spectral6,sector))
    
    b.xgrid.grid_line_color = None
    b.xaxis.major_label_orientation = pi/2.5
    b.xaxis.major_label_text_align = 'left'
    b.y_range.start = 0
    
    m=row(p)
    #show(m)
    
    #Plot matplotlib line graph
    rain_analysis_mat(rain_data_alloc_to_Sector)
    
    
    import folium
    from folium import Choropleth, Circle, Marker
    from folium.plugins import HeatMap, MarkerCluster
    
    m_2 = folium.Map(location=[18.5, 73.9], tiles='StamenTerrain', zoom_start=12) #StamenTerrain, StamenToner, StamenWatercolor
    
    #map_gdf_admin = map_df[['name','geometry']].set_index('name')
    map_gdf_sector = map_df_sector[['Sector','geometry']].set_index('Sector')
            
    #admin_count = map_df.name.value_counts()
    sector_count = map_df_sector.Sector.value_counts()        
    
    Choropleth(geo_data = map_gdf_sector.__geo_interface__,
               data = sector_count,
               key_on="feature.id",
               fill_color = 'YlGn',
               fill_opacity=0,
               line_opacity=0.2,
               #legend_name = 'Jo count per state',
               smooth_factor=0).add_to(m_2)
    
    #https://python-visualization.github.io/folium/quickstart.html#Choropleth-maps
    folium.GeoJson(map_gdf_sector.__geo_interface__,
                   name='geojson'
                   ).add_to(m_2)
    
    folium_color = {'complete':'green','na':'orange'}
    rain_data_total.apply(lambda row:folium.CircleMarker(location=[row["Lat"], row["Long"]], 
                                                   radius=5,
                                                   color=folium_color[row['Obs Status']],
                                                   popup=row['Obs Status']).add_to(m_2), axis=1)
    # ref link -https://stackoverflow.com/questions/42756934/how-to-plot-lat-and-long-from-pandas-dataframe-on-folium-map-group-by-some-label
    
    m_2.save('static/pune_Chropleth.html')
    folium_html = m_2._repr_html_()
    
    
    
    #Plot output path
    #C:/Users/dell/AppData/Local/Temp/tmpzm9borp4.html
    return(m,folium_html)