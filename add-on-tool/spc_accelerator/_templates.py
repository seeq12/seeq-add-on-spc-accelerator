from seeq import spy, sdk
from spc_accelerator.backend import *
import json
import pandas as pd


def create_template(
    URL,
    display_dict,
    histogram,
    input_condition,
    start_select,
    end_select,
    workbook_button,
    workbook_id,
    histogram_dict,
):
    workbooks_api = sdk.WorkbooksApi(spy.client)
    wb = spy.workbooks.pull(URL, quiet=True)
    ws = wb[0].worksheets
    new_worksheet_ids = []
    for worksheet_name, item_ids in display_dict.items():
        display_df = spy.search(pd.DataFrame(item_ids, columns=["ID"]), quiet=True)[
            ["Name", "ID", "Type"]
        ].reset_index(drop=True)
        display_df["Lane"] = 1
        display_df["Axis Group"] = "A"
        display_df["Samples Display"] = "Line"
        display_df.at[7, "Samples Display"] = "Line and Sample"
        display_df["Line Style"] = "Long Dash"
        display_df.at[7, "Line Style"] = "Solid"
        display_df.at[0, "Color"] = "#00b050"
        display_df.loc[1:2, "Color"] = "#a9a9a9"
        display_df.loc[3:4, "Color"] = "#ffc000"
        display_df.loc[5:6, "Color"] = "#ff0000"
        if isinstance(input_condition.v_model, str):
            display_df.loc[7:8, "Color"] = "#4055a3"
            if len(display_df) > 9:
                display_df.loc[9:, "Color"] = "#ff0000"
        else:
            display_df.at[7, "Color"] = "#4055a3"
            if len(display_df) > 8:
                display_df.loc[8:, "Color"] = "#ff0000"
        worksheet = [w for w in ws if w.name == worksheet_name][0]
        new_worksheet_ids += [worksheet.id]
        worksheet.display_items = display_df
        worksheet.display_range = {"Start": start_select.value, "End": end_select.value}
    if histogram.v_model == True:
        for worksheet_name in histogram_dict:
            worksheet = [w for w in ws if w.name == worksheet_name][0]
            new_worksheet_ids += [worksheet.id]
            worksheet.display_range = {
                "Start": start_select.value,
                "End": end_select.value,
            }
    spy.workbooks.push(wb, quiet=True)
    first_new_worksheet = [w for w in ws if w.name == list(display_dict.keys())[0]][0]
    workbook_button.href = first_new_worksheet.url
    for worksheet in new_worksheet_ids:
        workstep_id = (
            workbooks_api.get_worksheet(workbook_id=workbook_id, worksheet_id=worksheet)
            .to_dict()["workstep"]
            .split("/")
            .pop(-1)
        )
        worksheet_data = workbooks_api.get_workstep(
            workbook_id=workbook_id, worksheet_id=worksheet, workstep_id=workstep_id
        ).to_dict()["data"]
        worksheet_data_dict = json.loads(worksheet_data)
        try:
            worksheet_data_dict["state"]["stores"]["sqTrendStore"]
        except:
            worksheet_data_dict["state"]["stores"]["sqTrendStore"] = {
                "labelDisplayConfiguration": {
                    "name": "off",
                    "asset": "off",
                    "assetPathLevels": 1,
                    "unitOfMeasure": "off",
                    "custom": "off",
                    "customLabels": [],
                },
                "showCapsuleLaneLabels": False,
            }
        try:
            worksheet_data_dict["state"]["stores"]["sqTrendStore"][
                "labelDisplayConfiguration"
            ]
        except:
            worksheet_data_dict["state"]["stores"]["sqTrendStore"][
                "labelDisplayConfiguration"
            ] = {
                "name": "off",
                "asset": "off",
                "assetPathLevels": 1,
                "unitOfMeasure": "off",
                "custom": "off",
                "customLabels": [],
            }
        try:
            worksheet_data_dict["state"]["stores"]["sqTrendStore"][
                "showCapsuleLaneLabels"
            ]
        except:
            worksheet_data_dict["state"]["stores"]["sqTrendStore"][
                "showCapsuleLaneLabels"
            ] = False
        worksheet_data_dict["state"]["stores"]["sqTrendStore"][
            "labelDisplayConfiguration"
        ]["name"] = "lane"
        worksheet_data_dict["state"]["stores"]["sqTrendStore"][
            "labelDisplayConfiguration"
        ]["unitOfMeasure"] = "axis"
        worksheet_data_dict["state"]["stores"]["sqTrendStore"][
            "showCapsuleLaneLabels"
        ] = True

    return worksheet_data_dict


def format_histogram_worksheet(histogram_id, signal_name, URL, workbook_id):
    workbooks_api = sdk.WorkbooksApi(spy.client)

    histogram = spy.search(
        {"Scoped To": workbook_id, "Name": f"{signal_name}: Mean"},
        quiet=True,
        all_properties=True,
    )
    push_histogram = spy.push(
        metadata=histogram,
        workbook=workbook_id,
        worksheet=f"{signal_name} Histogram",
        errors="catalog",
        quiet=True,
    )
    wb = spy.workbooks.pull(URL, quiet=True)

    try:
        ws = wb[0].worksheets[
            f"My Folder >> {wb[0]['Name']} >> {signal_name} Histogram"
        ]
    except:
        for sheet in wb[0].worksheets:
            if sheet["Name"] == f"{signal_name} Histogram":
                ws = sheet

    ws.display_items = pd.DataFrame(columns=["Name", "Type", "ID"])
    spy.workbooks.push(wb, quiet=True)
    worksheet_url = push_histogram.spy.workbook_url
    histogram_worksheet_id = worksheet_url.split("/").pop(-1)
    workstep_id = (
        workbooks_api.get_worksheet(
            workbook_id=workbook_id, worksheet_id=histogram_worksheet_id
        )
        .to_dict()["workstep"]
        .split("/")
        .pop(-1)
    )
    worksheet_data = workbooks_api.get_workstep(
        workbook_id=workbook_id,
        worksheet_id=histogram_worksheet_id,
        workstep_id=workstep_id,
    ).to_dict()["data"]
    worksheet_data_dict = json.loads(worksheet_data)
    try:
        worksheet_data_dict["state"]["stores"]["sqTrendTableStore"]
    except:
        worksheet_data_dict["state"]["stores"]["sqTrendTableStore"] = {"items": []}
    worksheet_data_dict["state"]["stores"]["sqTrendTableStore"] = {
        "items": [
            {
                "autoDisabled": False,
                "stack": False,
                "id": histogram_id,
                "name": "Histogram",
                "selected": False,
                "color": "#4055a3",
                "binConfig": {},
            }
        ]
    }
    replaced_worksheet_data = json.dumps(worksheet_data_dict)
    workbooks_api.create_workstep(
        workbook_id=workbook_id,
        worksheet_id=histogram_worksheet_id,
        body={"data": replaced_worksheet_data},
    )
