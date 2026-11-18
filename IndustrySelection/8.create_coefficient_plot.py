import plotly.graph_objects as go
import pandas as pd
from datetime import datetime


def create_figure(title):

    fig = go.Figure().update_layout(template ="plotly_white", title = title, title_x = 0.5, title_y = 0.95, title_font_weight = 600)
    fig.update_layout(width = 1500, height = 800)

    return fig



def touch_up_figure(fig):

    fig.update_layout(margin=dict(t=50, b=80, l=300, r=50))
    fig.update_layout(margin = dict(autoexpand = False))
    fig.update_layout(paper_bgcolor = "#FFFFFF")
    fig.update_layout(plot_bgcolor = "#FFFFFF")
    fig.update_layout(font_family = "Garamond", font_weight = 1000, font_size = 19)
    fig.update_yaxes(tickfont = dict(size = 18, weight = 600))
    fig.update_xaxes(title_font = dict(size = 20, weight = 600), title_text = "Regression Coefficient", title_standoff = 20)
    fig.update_layout(legend2 = dict(orientation = "h", y = -0.1, x = 0.36, font_color = "#9C2225", font_size = 17))
    fig.update_yaxes(ticksuffix = " ")
    fig.update_xaxes(showgrid=False, zeroline=False, title_font = dict(color='#FFFFFF'), tickcolor = "#FFFFFF", tickfont = dict(color='#FFFFFF'))
    fig.update_yaxes(showgrid=False, zeroline=False, title_font = dict(color='#FFFFFF'), tickcolor = "#FFFFFF", tickfont = dict(color='#FFFFFF'))
    fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')


def plot_coefficient_dataframe(df, fig):
    
    for index, row in df.iterrows():

        if row["pval"] < 0.05:
            color = "#00C805"

        else:
            color = "#FFFFFF"


        fig.add_trace(
            go.Scatter(
                x=[row["coef"]], 
                y=[f'<span style="color:{color};">{index}</span>'],
                mode = "markers",
                error_x = dict(
                    type="data",
                    symmetric = False,
                    array = [row["err_left"]],
                    arrayminus = [row["err_right"]],
                    width = 6,
                    thickness = 3),
                showlegend = False,
                line = dict(
                    width = 10, 
                    color = color),
                name = index,
                marker = dict(size = 7),
                legend = "legend1"))


    fig.add_trace(
        go.Scatter(
            x=[None], 
            y = [None],
            mode = "markers",
            name = "Significant (p < 0.05)",
            marker = dict(color = "#9C2225"),
            legend = "legend2",
            showlegend=False,
        )
    )
        

    fig.add_vline(
        x=0,
        line = dict(width = 3, dash = "dash"),
        opacity = 0.5,
        annotation_text = "Null",
        annotation_position = "top",
        annotation_font = dict(size = 15),
        line_color = "#FFFFFF",
        annotation = dict(font_color = "#FFFFFF")
    )


    fig.update_yaxes(autorange = "reversed")


    touch_up_figure(fig)



def main():
    
    coefficient_df = pd.read_parquet("../data/10.regression_results.parquet")
    fig = create_figure("")
    plot_coefficient_dataframe(coefficient_df, fig)
    js = '''document.body.style.backgroundColor = "#101512"; '''
    #fig.show(renderer="browser", post_script=[js])
    fig.write_image(f"../plots/{datetime.now().strftime("%Y-%m-%d--%H-%M-%S")}.png", width = 1500, height = 1300, scale = 6)


main()