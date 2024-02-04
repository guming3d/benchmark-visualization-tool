from flask import Flask, render_template, request
import json
import pandas as pd
import plotly.express as px
from plotly.utils import PlotlyJSONEncoder
import json
from datetime import datetime

app = Flask(__name__)

def cleanse_jsonl(data: str) -> str:
    # because passing a whole file as a string is obviously peak efficiency
    clean_lines = []
    for line in data.splitlines():
        try:
            json.loads(line)  # oh look, it's json or it's junk
            clean_lines.append(line)
        except json.JSONDecodeError:
            # another one bites the dust, thank heavens
            pass

    # returning clean data because writing it back to a file was too mainstream
    return '\n'.join(clean_lines)

def load_jsonl_data(data: str):
    # data as a string, because who needs files anyway
    data_frames = []
    for line in data.splitlines():
        json_obj = json.loads(line)  # magic, turning strings into dicts

        # look at us, flattening jsons like it's pancake day
        flattened_obj = pd.json_normalize(json_obj, sep="_")
        data_frames.append(flattened_obj)

    # stitching data frames together, like a patchwork of mediocrity
    df = pd.concat(data_frames, ignore_index=True)
    return df

def create_figure(df, x_column, y_columns, title):
    # Ensure the specified columns are numeric, converting non-numeric values to NaN
    for col in y_columns:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # Use Plotly Express to create the figure
    fig = px.line(
        df,
        x=x_column,
        y=y_columns,
        labels={
            "value": title,
            "variable": "Metrics",
        },  # Customize label names as needed
        title=title,
    )

    # Update line names for clarity
    fig.for_each_trace(lambda t: t.update(name=t.name.replace("variable=", "")))

    return fig

def create_figure_util(df, x_column, y_columns, title):
    for col in y_columns:
        # Check if the column contains percentage values
        if df[col].dtype == "object" and df[col].str.contains("%").any():
            # Convert percentage strings to float, handling 'n/a' and other non-convertible strings
            df[col] = (
                df[col]
                .str.rstrip("%")
                .apply(lambda x: pd.to_numeric(x, errors="coerce"))
                / 100.0
            )
        else:
            # Convert column to numeric, coercing errors to NaN
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # Use Plotly Express to create the figure
    fig = px.line(
        df,
        x=x_column,
        y=y_columns,
        labels={
            "value": title,
            "variable": "Metrics",
        },  # Customize label names as needed
        title=title,
    )

    # Update line names for clarity
    fig.for_each_trace(lambda t: t.update(name=t.name.replace("variable=", "")))

    # Set y-axis range to have a maximum of 100 (assuming it's percentage)
    fig.update_layout(
        yaxis_range=[0, 1]
    )  # yaxis_range is [min, max], setting max to 1 since the data is now in decimal form

    return fig

def get_current_time_formatted():
    now = datetime.now()
    formatted_time = now.strftime("%Y-%m-%d-%H-%M")
    return formatted_time

def process_jsonl_and_create_figures(content : str):
    content = cleanse_jsonl(content)
    df = load_jsonl_data(content)
    
    fig_tpm = create_figure(df, "timestamp", ["tpm_total", "tpm_context", "tpm_gen"], "TPM over Time")
    graphJSON_tpm = json.dumps(fig_tpm, cls=PlotlyJSONEncoder)
    
    fig_util = create_figure_util(df, "timestamp", ["util_avg", "util_95th"], "Utilization over Time")
    graphJSON_util = json.dumps(fig_util, cls=PlotlyJSONEncoder)

    fig_ttft = create_figure(df, "timestamp", ["ttft_avg", "ttft_95th"], "Time To First Token")
    graphJSON_ttft = json.dumps(fig_ttft, cls=PlotlyJSONEncoder)
    
    fig_e2e = create_figure(df, "timestamp", ["e2e_avg", "e2e_95th"], "e2e over Time")
    graphJSON_e2e = json.dumps(fig_e2e, cls=PlotlyJSONEncoder)
    
    current_time = get_current_time_formatted()
    
    return {
        "graphJSON_tpm": graphJSON_tpm,
        "graphJSON_util": graphJSON_util,
        "graphJSON_ttft": graphJSON_ttft,
        "graphJSON_e2e": graphJSON_e2e,
        "formatted_time": current_time
    }
    
@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        # Handle file upload or text input
        content = request.form.get('content')  # Assuming text input is named 'content'
        
        if 'file' in request.files:
            file = request.files['file']
            if file.filename:
                content = file.read().decode('utf-8')

        if content:
            try:
                # Process the JSONL data
                figures = process_jsonl_and_create_figures(content)

                # Render the template with graphs data
                return render_template(
                    "index.html",
                    graphJSON_tpm=figures["graphJSON_tpm"],
                    graphJSON_util=figures["graphJSON_util"],
                    graphJSON_ttft=figures["graphJSON_ttft"],
                    graphJSON_e2e=figures["graphJSON_e2e"],
                    formatted_time=figures["formatted_time"],
                )
            except Exception as e:
                # Output the exception stack to the user
                return f"An error occurred: {str(e)}"
        else:
            # No content provided, do nothing
            return render_template("start.html")
    else:
        # For GET requests, 'graphs' is not needed, so pass an empty dictionary or None
        return render_template("start.html")

if __name__ == '__main__':
    app.run(debug=True)
