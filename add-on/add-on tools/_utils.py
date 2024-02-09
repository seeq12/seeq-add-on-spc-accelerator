from seeq import spy
from seeq import sdk
import json
from datetime import datetime
    
def pull_worksheet_data(URL, workbook_id, worksheet_id):        
    workbooks_api = sdk.WorkbooksApi(spy.client)

    try:
        worksheet_items = spy.search(URL, quiet=True)
        signals = worksheet_items[worksheet_items['Type'].str.contains('Signal')]
        signal_list = signals['Name'].to_list()
        conditions = worksheet_items[worksheet_items['Type'].str.contains('Condition')]
        condition_list = conditions['Name'].to_list()
        workstep_id = workbooks_api.get_worksheet(workbook_id=workbook_id, worksheet_id=worksheet_id).to_dict()['workstep'].split('/').pop(-1)
        data = workbooks_api.get_workstep(workbook_id=workbook_id, worksheet_id=worksheet_id, workstep_id=workstep_id).to_dict()['data']
        data_dict = json.loads(data)
        start = data_dict['state']['stores']['sqDurationStore']['displayRange']['start']
        end = data_dict['state']['stores']['sqDurationStore']['displayRange']['end']
        start_time = datetime.fromtimestamp(start/1000).astimezone()
        end_time = datetime.fromtimestamp(end/1000).astimezone()

        return signal_list, condition_list, start_time, end_time, signals, conditions
    except Exception as e:
        raise RuntimeError(f"Error occurred while retrieving worksheet data: {str(e)}")