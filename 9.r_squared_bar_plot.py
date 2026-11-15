import plotly.graph_objects as go
import numpy as np
import json
import sys
from datetime import datetime



def create_figure(title):

    fig = go.Figure().update_layout(template ="plotly_white", title = title, title_x = 0.5, title_y = 0.95, title_font_weight = 600)
    fig.update_layout(width = 1200, height = 800)

    return fig



def touch_up_figure(fig):

    fig.update_layout(margin=dict(t=50, b=80, l=250, r=120))
    fig.update_layout(margin = dict(autoexpand = False))
    fig.update_layout(paper_bgcolor = "#FFFFFF")
    fig.update_layout(plot_bgcolor = "#FFFFFF")
    fig.update_layout(font_family = "Garamond", font_weight = 1000, font_size = 19)
    fig.update_yaxes(tickfont = dict(size = 15, weight = 600))
    fig.update_xaxes(title_font = dict(size = 17, weight = 800), title_standoff = 20, title_text = r"$\mathbf{|\%\Delta|}\ \textbf{in}\ \mathbf{R^{\!2}}\ \textbf{after removing predictor}$")
    fig.update_layout(legend2 = dict(orientation = "h", y = -0.1, x = 0.36, font_color = "#9C2225", font_size = 19))
    fig.update_yaxes(ticksuffix = " ")


def create_bar_plot(fig, my_dict):

    significants = ["Consumer Lending", "Retail Brokerage", "Alternative Asset Managers", "Specialty Finance", "Crypto Exchanges", "Regional Banks", "Mortgage REITs"]

    for industry in my_dict:

        if industry in significants:
            color = "#9C2225"
        else:
            color = "#012F68"

        fig.add_trace(
            go.Bar(
                x = [my_dict[industry]],
                y = [f'<span style="color:{color};">{industry}</span>'],
                marker = dict(
                    color = color,
                ),
                orientation = "h",
                name = industry,
                legend = "legend1",
                showlegend=False
            )
        )

    
    annotations = []

    for val, lab in zip(np.round(list(my_dict.values()), decimals = 2), list(my_dict.keys())):

        if lab in significants:
            color = "#9C2225"
        else:
            color = "#012F68"

        annotations.append(dict(
                        y=f'<span style="color:{color};">{lab}</span>', 
                        x= val + 0.2,
                        text= str(val) + '%',
                        font=dict(family='Garamond', size=16,
                                    color=color),
                        showarrow=False))

    fig.update_layout(annotations = annotations)

    touch_up_figure(fig)


def get_data():

    with open(f"data/11.r_squared_changes.json") as f:
        data = json.load(f)

    return data



def sort_dictionary(my_dict):

    my_dict.pop("all")

    return dict(sorted(my_dict.items(), key=lambda x: x[1]))



def main():

    fig = create_figure("")
    data = sort_dictionary(get_data())
    create_bar_plot(fig, data)
    fig.show()
    fig.write_image(f"plots/{datetime.now().strftime("%Y-%m-%d--%H-%M-%S")}.png", width = 1200, height = 800, scale = 6)

main()
