import dash
from dash import dcc
from dash import html
from dash import dash_table
from dash.dependencies import Input, Output
import pandas as pd
import plotly.express as px
import folium
from folium import plugins
from folium.plugins import HeatMap, MarkerCluster
from dash.dash_table.Format import Group
import dash_bootstrap_components as dbc

# 데이터 불러오기
df = pd.read_csv("2_busan_heat_island_csv.csv", encoding='cp949')

# '구' 칼럼을 기준으로 데이터프레임을 그룹화하고, 각 그룹의 크기를 계산
df_grouped = df.groupby('구').size().reset_index(name='counts')

# 컬러 매핑
color_mapping = {
    '금정구':'red',
    '해운대구':'orange',
    '동구':'green',
    '강서구':'blue',
    '사상구':'purple',
}

# 히스토그램 생성
fig = px.histogram(df_grouped, x='구', y='counts', color='구', color_discrete_map=color_mapping, height=400, width=600)

# Folium 지도 객체 생성
m = folium.Map(location=[35.2, 129], zoom_start=11)
for lat, lon, loc in zip(df['latitude'], df['longitude'], df['address']):
    folium.Marker(location=[lat, lon], popup=folium.Popup(loc, max_width=200)).add_to(m)
m = m._repr_html_()

m1 = folium.Map(location=[35.2, 129], zoom_start=11)
mc = MarkerCluster()
for _, row in df.iterrows():
    folium.Marker(location=[row['latitude'], row['longitude']], popup=folium.Popup(row['address'], max_width=200)).add_to(mc)
mc.add_to(m1)
m1 = m1._repr_html_()

m2 = folium.Map(location=[35.2, 129], zoom_start=11)
HeatMap(data=df[['latitude', 'longitude']], radius=20).add_to(m2)
m2 = m2._repr_html_()

m3 = folium.Map(location=[35.2, 129], zoom_start=11)
for _, row in df.iterrows():
    area = row['구']
    color = color_mapping.get(area)
    folium.Marker(
        location=[row['latitude'], row['longitude']],
        popup=folium.Popup(row['address'], max_width=200),
        icon=folium.Icon(color=color)
    ).add_to(m3)
m3 = m3._repr_html_()

# 대시 애플리케이션 생성
app = dash.Dash(__name__)

# '구'의 목록 가져오기
gu_list = df['구'].unique()

app.layout = html.Div([
    dcc.Dropdown(
        id='gu-dropdown',
        options=[{'label': i, 'value': i} for i in gu_list],
        value=gu_list[0]
    ),
    html.Button('확인', id='confirm-button', n_clicks=0),
    dash_table.DataTable(id='table'),
    dcc.Graph(figure=fig),
    html.Iframe(id='m', srcDoc=m, style={"height": "200px", "width": "30%"}),
    html.Iframe(id='m1', srcDoc=m1, style={"height": "200px", "width": "30%"}),
#    dcc.Store(id='m1-store'),
    dcc.Store(id='m-store'),
    html.Iframe(id='m2', style={"height": "200px", "width": "30%"}),
    html.Iframe(id='m3', srcDoc=m3, style={"height": "200px", "width": "30%"})
])

@app.callback(
    Output('table', 'data'),
    Output('table', 'columns'),
    Input('confirm-button', 'n_clicks'),
    Input('gu-dropdown', 'value')
)

def update_table(n_clicks, selected_gu):
    if n_clicks > 0:
        selected_df = df[df['구'] == selected_gu][['구', 'address', '지역특성']]
        data = selected_df.to_dict('records')
        columns = [{"name": i, "id": i} for i in selected_df.columns]
        return data, columns
    return [], []




# 'm' 지도 생성
@app.callback(
    Output('m-store', 'data'),
    Input('confirm-button', 'n_clicks'),
    Input('gu-dropdown', 'value')
)
def update_map(n_clicks, selected_gu):
    if n_clicks > 0:
        selected_df = df[df['구'] == selected_gu]
        center_lat = selected_df['latitude'].mean()
        center_lon = selected_df['longitude'].mean()

        m = folium.Map(location=[center_lat, center_lon], zoom_start=13)
        for lat, lon, loc in zip(selected_df['latitude'], selected_df['longitude'], selected_df['address']):
            folium.Marker(location=[lat, lon], popup=folium.Popup(loc, max_width=200)).add_to(m)
        return m._repr_html_()
    return folium.Map(location=[35.2, 129], zoom_start=11)._repr_html_()

@app.callback(
    Output('m', 'srcDoc'),
    Input('m-store', 'data')
)
def update_iframe(src):
    return src

# 지역특성별 색상 매핑
feature_color_mapping = {
    '공항 일대':'blue',
    '공장 지대':'red',
    '항만 일대' : 'purple',
    '도매시장':'pink',
   
}

# 지역특성에 따른 히스토그램 생성
fig_feature = px.histogram(df, x='지역특성', color='지역특성', color_discrete_map=feature_color_mapping, height=400, width=600)

m_feature_map = folium.Map(location=[35.2, 129], zoom_start=11)
for _, row in df.iterrows():
    feature = row['지역특성']
    color = feature_color_mapping.get(feature, 'gray')  # 지역특성에 따른 색상을 가져오되, 매핑이 없으면 'gray'를 기본값으로 사용합니다.
    folium.Marker(
        location=[row['latitude'], row['longitude']],
        popup=folium.Popup(row['address'], max_width=200),
        icon=folium.Icon(color=color)
    ).add_to(m_feature_map)
m_feature_map = m_feature_map._repr_html_()

#layout
app.layout = dbc.Container([
    html.Div(html.H1("부산 열섬 현황"), className="text-center py-4", style={"text-align": "center"}),   # 제목 추가
    html.Hr(),

    dbc.Row([
        dbc.Col(html.Div(html.Iframe(id='m1', srcDoc=m1, style={"height": "300px", "width": "40%"}), style={"display": "flex", "justify-content": "center"})),
    ], justify="center"),

    dcc.Store(id='m1-store'),
    html.Br(),
    html.Hr(),

    html.H3("행정구별 열섬 현황", className="text-center py-4", style={"text-align": "center"}),
    dbc.Row([
        dbc.Col(html.Div(dcc.Graph(figure=fig), style={"width": "80%"}), style={"display": "flex", "justify-content": "center"}),  # 행정구별 열섬 개수 비교 히스토그램
        dbc.Col(html.Div(html.Iframe(id='m3', srcDoc=m3, style={"height": "300px", "width": "40%"}), style={"display": "flex", "justify-content": "center"})),
    ], justify="center"),
    html.Br(),
    html.Hr(),

    html.H3("행정구별 열섬 세부사항", className="text-center py-4", style={"text-align": "center"}),
    dbc.Row([  # 드롭다운
        dbc.Col([
            dcc.Dropdown(
                id='gu-dropdown',
                options=[{'label': i, 'value': i} for i in gu_list],
                value=gu_list[0]
            ),
        ], width=6),
        dbc.Col([
            html.Button('확인', id='confirm-button', n_clicks=0),
        ], width=6)
    ], justify="center"),
    html.Br(),

    dbc.Row([
        dbc.Col(dash_table.DataTable(id='table'), width=6),  # 테이블
        dbc.Col(html.Div(html.Iframe(id='m', srcDoc=m, style={"height": "300px", "width": "40%"}), style={"display": "flex", "justify-content": "center"})),  # 'm' 지도
    ], justify="center"),
    dcc.Store(id='m-store'),
    html.Br(),
    html.Hr(),

    html.H3("지역 특성별 열섬 세부사항", className="text-center py-4", style={"text-align": "center"}),
    dbc.Row([
        dbc.Col(html.Div(dcc.Graph(figure=fig_feature), style={"width": "80%"}), style={"display": "flex", "justify-content": "center"}),  # 지역특성에 따른 히스토그램
        dbc.Col(html.Div(html.Iframe(id='m_feature_map', srcDoc=m_feature_map, style={"height": "300px", "width": "40%"}), style={"display": "flex", "justify-content": "center"})),  # 지역특성에 따른 'm_feature_map' 지도
    ], justify="center"),
], fluid=True)


app.run_server(debug=True, use_reloader=False)
