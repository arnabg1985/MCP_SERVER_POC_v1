from flask import Flask, request, jsonify
import pandas as pd

app = Flask(__name__)

CSV_FILE = "financial_application_logs.csv"
df = pd.read_csv(CSV_FILE, parse_dates=['date'])

def filter_logs(filters, date_range=None, time_range=None):
    filtered = df
    for key, value in filters.items():
        filtered = filtered[filtered[key] == value]
    if date_range:
        if date_range.get('start'):
            filtered = filtered[filtered['date'] >= date_range['start']]
        if date_range.get('end'):
            filtered = filtered[filtered['date'] <= date_range['end']]
    if time_range:
        if time_range.get('start'):
            filtered = filtered[filtered['time_stamp'] >= time_range['start']]
        if time_range.get('end'):
            filtered = filtered[filtered['time_stamp'] <= time_range['end']]
    return filtered

def parse_date_params():
    date_range = {}
    try:
        if 'start_date' in request.args:
            date_range['start'] = pd.to_datetime(request.args.get('start_date'))
        if 'end_date' in request.args:
            date_range['end'] = pd.to_datetime(request.args.get('end_date'))
    except Exception:
        return None, jsonify({'error': 'Invalid date format. Use YYYY-MM-DD'}), 400
    return date_range, None, None

def parse_time_params():
    time_range = {}
    if 'start_time' in request.args:
        time_range['start'] = request.args.get('start_time')
    if 'end_time' in request.args:
        time_range['end'] = request.args.get('end_time')
    return time_range

@app.route('/logs/', methods=['GET'])
def get_logs():
    date_range, err, code = parse_date_params()
    if err:
        return err, code
    time_range = parse_time_params()
    limit = int(request.args.get('limit', 100))
    filtered = filter_logs({}, date_range, time_range)
    return jsonify(filtered.head(limit).to_dict(orient="records"))

@app.route('/logs/app/<app_name>', methods=['GET'])
def logs_by_app(app_name):
    date_range, err, code = parse_date_params()
    if err:
        return err, code
    time_range = parse_time_params()
    limit = int(request.args.get('limit', 100))
    filters = {'application_name': app_name}
    filtered = filter_logs(filters, date_range, time_range)
    return jsonify(filtered.head(limit).to_dict(orient="records"))

@app.route('/logs/app/<app_name>/level/<log_level>', methods=['GET'])
def logs_by_app_level(app_name, log_level):
    date_range, err, code = parse_date_params()
    if err:
        return err, code
    time_range = parse_time_params()
    limit = int(request.args.get('limit', 100))
    filters = {'application_name': app_name, 'log_level': log_level}
    filtered = filter_logs(filters, date_range, time_range)
    return jsonify(filtered.head(limit).to_dict(orient="records"))

@app.route('/logs/app/<app_name>/server/<server>', methods=['GET'])
def logs_by_app_server(app_name, server):
    date_range, err, code = parse_date_params()
    if err:
        return err, code
    time_range = parse_time_params()
    limit = int(request.args.get('limit', 100))
    filters = {'application_name': app_name, 'servernames': server}
    filtered = filter_logs(filters, date_range, time_range)
    return jsonify(filtered.head(limit).to_dict(orient="records"))

@app.route('/logs/app/<app_name>/severity/<severity>', methods=['GET'])
def logs_by_app_severity(app_name, severity):
    date_range, err, code = parse_date_params()
    if err:
        return err, code
    time_range = parse_time_params()
    limit = int(request.args.get('limit', 100))
    filters = {'application_name': app_name, 'severity': severity}
    filtered = filter_logs(filters, date_range, time_range)
    return jsonify(filtered.head(limit).to_dict(orient="records"))

@app.route('/logs/app/<app_name>/level/<log_level>/server/<server>/severity/<severity>', methods=['GET'])
def logs_by_all_filters(app_name, log_level, server, severity):
    date_range, err, code = parse_date_params()
    if err:
        return err, code
    time_range = parse_time_params()
    limit = int(request.args.get('limit', 100))
    filters = {
        'application_name': app_name,
        'log_level': log_level,
        'servernames': server,
        'severity': severity
    }
    filtered = filter_logs(filters, date_range, time_range)
    return jsonify(filtered.head(limit).to_dict(orient="records"))

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)