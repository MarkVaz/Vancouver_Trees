# -*- coding: utf-8 -*-
"""
Created on Thu Jul 14 21:59:37 2022

@author: MC
"""

#Lets import the nescessary libraries for my project!
import streamlit as st
import altair as alt
import pandas as pd
import json






alt.themes.enable('dark')

#Now lets import our data into a pandas dataframe
data_url = 'https://raw.githubusercontent.com/UBC-MDS/exploratory-data-viz/main/data/vancouver_trees.csv'

trees = pd.read_csv(data_url, parse_dates = ['date_planted'])

trees = trees.head(5000)
#To answer our questions we will need to use certain columns quite a bit, to save some typing lets adjust some column names!
trees_df = trees

trees_df = trees_df.rename(columns = {'neighbourhood_name':'neighbourhood','species_name':'species'})

#Lets remove the uppercase lettering from a few columns as well!
trees_df['species'] = trees_df['species'].str.title()
trees_df['common_name'] = trees_df['common_name'].str.title()

#Since we only need the year in the data_planted column lets convert those values
trees_df['date_planted'] = trees_df['date_planted'].dt.year

trees_df = trees_df.rename(columns = {'date_planted':'year_planted'})

trees_df['year_planted'] = pd.to_datetime(trees_df['year_planted'], format = '%Y')

#This is a simple visualization that we can use as a selection for our future visualizations!


#This creates a slider that controls the number of neighbourhoods visible in the visualization!
neighbourhood_slider = alt.binding_range(step=1, 
                                         min=5, 
                                         max=22,
                                         name = 'Number of Neighbourhoods')

select_neighbourhoods = alt.selection_single(fields=['neighbourhood'], 
                                     bind = neighbourhood_slider, 
                                     init = {'neighbourhood' : 15} 
                                     )

#This creates the ability to click a specific neighbourhood to alter future visualizations
select_neighbourhood_click = alt.selection_multi(encodings=["y"], on='click', nearest=True)


#Lets create our chart now!

neighbourhood_count = (alt.Chart(trees_df)
                       
                       .mark_bar(height = 15)
                       
                       .encode(x = alt.X('neighbour_count:Q', title = 'Number of Trees'),
                               y = alt.Y('neighbourhood', sort = '-x', title = 'Neighbourhood'),
                               color = alt.condition(select_neighbourhood_click,
                                                     alt.Color('neighbour_count:Q',
                                                               scale = alt.Scale(scheme = 'yellowgreen')), 
                                                     alt.value("grey")
                                                    ),
                               tooltip = ['neighbour_count:Q']
                              )
                       
                       .transform_aggregate(neighbour_count="count()", 
                                            groupby=["neighbourhood"])
                       
                       .properties(title = { 'text' : 'Number of Trees per Neighbourhood',
                                             'subtitle' : ('Click on a bar to alter other charts!','Double click once selected to return to the original chart')})
                       
                       .transform_window(rank='rank(neighbour_count)', 
                                         sort=[alt.SortField("neighbour_count", order="descending")])
                       
                       .add_selection(select_neighbourhoods)
                       
                       .add_selection(select_neighbourhood_click)
                       
                       .transform_filter(alt.datum.rank <= select_neighbourhoods.neighbourhood)
                       
                       
                      
                      )
#Lets make a chart that takes the top 10 Species of trees!
species_count_10 = (alt.Chart(trees_df, height = 200)
                     .mark_bar()
                     
                     .transform_filter(select_neighbourhood_click)
                    
                     .encode(x = alt.X('species',
                                       sort = '-y',
                                       title = 'Species Name'),
                             y = alt.Y('species_count:Q', 
                                       title = 'Number of Trees'),
                             color = alt.Color('species_count:Q',
                                               scale = alt.Scale(scheme = 'bluegreen'),
                                               title = 'Count'),
                             tooltip = ['species_count:Q']
                            )
                     .properties(title = 'Number of Trees by Species')
                    
                     .transform_aggregate(species_count="count()", 
                                             groupby=["species"])
                       
                     .transform_window(rank="rank(species_count)", 
                                   sort=[alt.SortField("species_count", order="descending")])
                       
                     .transform_filter(alt.datum.rank <= 15)
                    
                     
                   )
#Now lets align our charts side by side
two_charts = (alt.hconcat(neighbourhood_count, species_count_10)
              .resolve_legend(color = 'independent')
              .resolve_scale(color = 'independent'))

url_geojson = 'https://raw.githubusercontent.com/UBC-MDS/exploratory-data-viz/main/data/local-area-boundary.geojson'

data_geojson_remote = alt.Data(url=url_geojson, format=alt.DataFormat(property='features',type='json'))

vancouver_map = alt.Chart(data_geojson_remote).mark_geoshape(
    color = 'lightgray', opacity= 0.5, stroke='white').encode().project(type='identity', reflectY=True)

#Now we can bring in our data for each tree!

#Lets also add an option that shows only Serrulata Trees since Cherry Blossoms are the most popular!
options_list = [None,'Serrulata']


radio_bind = alt.binding_radio(options = options_list, name = 'Select:', labels = ['All Trees','Only Cherry Blossoms'])
radio_select = alt.selection_single(fields = ['species'], bind = radio_bind)

map_chart = (alt.Chart(trees_df)
                 .mark_circle(size = 2, color = 'lightgreen')
                 
                 .encode(longitude = 'longitude',
                         latitude = 'latitude',
                         tooltip =  ['neighbourhood']
                        )
                 .properties(title = 'Geolocation of Trees in Vancouver')
                 .project(type= 'identity', reflectY=True)
                 .add_selection(radio_select, select_neighbourhood_click)
                 .transform_filter(radio_select)
                 .transform_filter(select_neighbourhood_click)
                 
                 
                 
                )

final_map = (vancouver_map + map_chart)

#Lets make our final chart for our dashboard
planted_chart = (alt.Chart(trees_df, width = 400, height = 200)
                .mark_bar()
                .transform_filter(select_neighbourhood_click)                
                .encode(x =  alt.X('year_planted', title = 'Year Planted'),
                        y =  alt.Y('count()',                                 
                                   title = 'Number of Trees'),
                        tooltip = ['count()','year_planted']
                        
                       )
                .properties(title = 'Trees Planted per Year')
                .add_selection(select_neighbourhood_click)
                )
#First we add the two secondary charts together vertically
right_chart = (alt.vconcat(planted_chart, species_count_10)
              .resolve_legend(color = 'independent')
              .resolve_scale(color = 'independent'))
left_chart = (alt.vconcat(neighbourhood_count , final_map)
              .resolve_legend(color = 'independent')
              .resolve_scale(color = 'independent'))
#Then we concatonate horizontally with our main chart to create a dashboard
dashboard = (alt.hconcat(left_chart, right_chart)
             .resolve_legend(color = 'independent')
             .resolve_scale(color = 'independent'))

Header = st.container()
Code = st.container()
Dashboard = st.container()
Footer = st.container()

with Header:
    st.title("Becoming a Vancouver Arborista!")
    st.text("This project analyzes 5000 data entries of trees in the city of Vancouver")
    st.text("Using Altair and Pandas, I hope to show some insight into the beautiful trees in Vancity")
    st.text("Below is a link to the data source, used for this project")
   
    st.markdown('https://raw.githubusercontent.com/UBC-MDS/data_viz_wrangled/main/data/Trees_data_sets/small_unique_vancouver.csv' ,unsafe_allow_html=True)
    st.text("For best view of the page on desktop go to settings in the top right, and click on wide mode")
    st.text('Hope you enjoy the data visualizations!')
    st.text('-M.Vaz')


    
with Dashboard:
    st.altair_chart(dashboard, use_container_width = True)

