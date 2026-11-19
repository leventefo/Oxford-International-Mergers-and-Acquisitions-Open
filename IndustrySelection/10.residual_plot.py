import plotly.graph_objects as go
import numpy as np
import json
import sys
from datetime import datetime
import statsmodels.api as sm



def create_figure(title):

    fig = go.Figure().update_layout(template ="plotly_white", title = title, title_x = 0.5, title_y = 0.95, title_font_weight = 600)
    fig.update_layout(width = 1500, height = 800)

    return fig



def touch_up_figure(fig):

    fig.update_layout(margin=dict(t=50, b=80, l=300, r=120))
    fig.update_layout(margin = dict(autoexpand = False))
    fig.update_layout(paper_bgcolor = "#FFFFFF")
    fig.update_layout(plot_bgcolor = "#FFFFFF")
    fig.update_layout(font_family = "Garamond", font_weight = 1000, font_size = 19)
    fig.update_yaxes(tickfont = dict(size = 18, weight = 600), title_text = "Residual")
    fig.update_xaxes(title_font = dict(size = 20, weight = 800), title_standoff = 25, title_text = "Fitted Return")
    fig.update_layout(legend2 = dict(orientation = "h", y = -0.1, x = 0.36, font_color = "#9C2225", font_size = 19))
    fig.update_yaxes(ticksuffix = "   ")
    fig.update_xaxes(showgrid=False, zeroline=False, title_font = dict(color='#FFFFFF'), tickcolor = "#FFFFFF", tickfont = dict(color='#FFFFFF'))
    fig.update_yaxes(showgrid=False, zeroline=False, title_font = dict(color='#FFFFFF'), tickcolor = "#FFFFFF", tickfont = dict(color='#FFFFFF'))
    fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')


def create_residual_plot(fig, results):

    fig.add_trace(
        go.Scatter(
            x = results.fittedvalues,
            y = results.resid,
            mode = "markers",
            marker = dict(color = "#00C805")
        ))

    fig.add_hline(y=0, line_dash="dash", line_color="#FFFFFF", line = dict(width = 3, dash = "dash"))


    touch_up_figure(fig)


def get_regression_data():

    with open(f"../data/regression_results.pickle") as f:
        data = json.load(f)

    return data



def main():

    fig = create_figure("")
    results = sm.load("../data/regression_results.pickle")
    create_residual_plot(fig, results)
    js = '''document.body.style.backgroundColor = "#202825"; '''
    fig.show(renderer="browser", post_script=[js])
    fig.write_image(f"../plots/{datetime.now().strftime("%Y-%m-%d--%H-%M-%S")}.png", width = 1500, height = 800, scale = 6)

main()
