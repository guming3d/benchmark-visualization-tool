from flask import Flask, render_template, request
import json

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        # Handle file upload or text input
        print("received a POST message")
        content = request.form.get('content')  # Assuming text input is named 'content'
        print(content)
        if 'file' in request.files:
            file = request.files['file']
            content = file.read().decode('utf-8')

        # Process the JSONL data
        processed_data = process_jsonl(content)

        # Generate diagrams
        graphs = generate_tpm_diagram(processed_data)

        # Render the template with graphs data
        return render_template('index.html', graphs=graphs)
    else:
        print("received a GET message")
        # For GET requests, 'graphs' is not needed, so pass an empty dictionary or None
        return render_template('index.html', graphs={})

def process_jsonl(content):
    data = []
    for line in content.splitlines():
        try:
            json_data = json.loads(line)
            data.append(json_data)
        except json.JSONDecodeError:
            continue  # Skip lines that are not valid JSON
    return data


def generate_diagrams(data):
    # Implement logic to generate diagrams
    pass

import plotly.graph_objs as go

def generate_tpm_diagram(data):
    # Example function to generate TPM diagram
    x_values = [d['timestamp'] for d in data]
    y_values = [d['tpm']['total'] for d in data]

    trace = go.Scatter(x=x_values, y=y_values, mode='lines+markers', name='Total TPM')
    layout = go.Layout(title='Total Transactions Per Minute (TPM)', xaxis=dict(title='Time'), yaxis=dict(title='TPM'))
    
    return {'data': [trace], 'layout': layout}

if __name__ == '__main__':
    app.run(debug=True)
