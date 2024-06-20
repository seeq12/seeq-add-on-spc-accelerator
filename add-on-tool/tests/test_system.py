import pandas as pd
import pytest
import warnings
import inspect

warnings.filterwarnings("ignore")

import ipyvuetify as v
import ipywidgets
from seeq import spy, sdk
from datetime import datetime, timedelta, timezone
from datetime import datetime

import sys
import os

from spc_accelerator import SPCAccelerator

timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")


# Define the fixture to setup the workbook and asset tree for testing
@pytest.fixture(scope="module")
def spc_accelerator_testing(request):
    def setup_workbook(workbook_name):
        # Create a new workbook
        create_workbook(workbook_name)

        # Search for the signal
        results = spy.search(
            {"Path": "SPC Addon", "Name": "*"},
            workbook=workbook_name,
            quiet=True,
            all_properties=True,
        )

        # Define the display window for the workbook
        time_now = datetime.now(timezone.utc)
        end_time = time_now - timedelta(hours=12)
        start_time = (end_time - timedelta(days=3)).strftime("%Y-%m-%d %H:%M")
        end_time_str = end_time.strftime("%Y-%m-%d %H:%M")
        time_now_str = time_now.strftime("%Y-%m-%d %H:%M")

        # Push the metadata DataFrame to a new workbook
        push_results = spy.push(
            metadata=results,
            workbook=workbook_name,
            worksheet=f"Test - {time_now_str}",
            quiet=True,
        )

        workbooks_df = spy.workbooks.search({"Name": workbook_name}, quiet=True)

        wb = spy.workbooks.pull(workbooks_df, quiet=True)

        # Find the workbook with the workbook_name
        workbook = next((w for w in wb if w.name == workbook_name), None)

        # Check if workbook is found
        if workbook is not None:
            # Find the worksheet that matches the end_time
            matching_worksheet = next(
                (
                    ws
                    for ws in workbook.worksheets
                    if f"Test - {time_now_str}" in ws.name
                ),
                None,
            )
            matching_worksheet.display_range = {"Start": start_time, "End": end_time}

        push_result = spy.workbooks.push(wb, quiet=True)

        push_url = push_result["URL"][0]
        workbook_id = spy.utils.get_workbook_id_from_url(push_url)
        worksheet_id = matching_worksheet.id

        # Extract the worksheet GUID from the url
        worksheet_guid = push_url.split("/worksheet/")[1].split("/")[0]

        # Replace the worksheet GUID in the url with the new worksheet ID
        url = push_url.replace(
            f"/worksheet/{worksheet_guid}", f"/worksheet/{worksheet_id}"
        )

        # Get the ID of the matching worksheet
        matching_worksheet_id = (
            matching_worksheet.id if matching_worksheet is not None else None
        )

        items_api = sdk.ItemsApi(spy.client)
        # Get a list of IDs of all worksheets that are not the matching worksheet
        non_matching_worksheet_ids = [
            ws.id for ws in workbook.worksheets if ws.id != matching_worksheet_id
        ]
        for ws in non_matching_worksheet_ids:
            items_api.archive_item(id=ws)

        return url, workbook_id, worksheet_id

    def create_workbook(workbook_name):
        # Search for the 'Temperature' signal in the Example asset tree
        search_results = spy.search(
            {"Path": "Example >> Cooling Tower 1 >> Area A", "Name": "Temperature"},
            quiet=True,
        )

        # Create a new asset tree called 'SPC Addon'
        addon_tree = spy.assets.Tree("SPC Addon", workbook=workbook_name, quiet=True)

        # Insert a new asset called 'Asset A' into the tree
        addon_tree.insert(children="Asset A", quiet=True)

        # Assign the 'Temperature' signal to 'Asset A'
        addon_tree.insert(children=search_results, parent="Asset A", quiet=True)

        # Insert a new condition called 'Temperature > 90' into 'Asset A'
        addon_tree.insert(
            name="Temperature > 75",
            formula="""($temp > 75).intersect(days())
    .transform($capsule ->
    $capsule.setProperty('Date','Date '+$capsule.property('start').tostring().replace('/(.*)(T.*)/','$1'))) """,
            formula_parameters={"$temp": "Temperature"},
            parent="Asset A",
            quiet=True,
        )

        # Insert a new condition called 'Days' into 'Asset A'
        addon_tree.insert(
            name="Days",
            formula="""days()
    .transform($capsule ->
    $capsule.setProperty('Date','Date '+$capsule.property('start').tostring().replace('/(.*)(T.*)/','$1')))""",
            formula_parameters={"$temp": "Temperature"},
            parent="Asset A",
            quiet=True,
        )

        # Push the asset tree to Seeq
        addon_tree.push(quiet=True)

    test_names = [
        f"test_spc_accelerator_object_created_successfully {timestamp}",
        f"test_missing_input_signal_training_window {timestamp}",
        f"test_create_control_chart_signal_only {timestamp}",
        f"test_create_control_chart_signal_condition {timestamp}",
        f"test_create_control_chart_we_runrules {timestamp}",
        f"test_create_control_chart_nelson_runrules {timestamp}",
        f"test_create_control_chart_histogram {timestamp}",
        f"test_create_control_chart_capsule_prop {timestamp}",
        f"test_create_control_chart_apply_condition {timestamp}",
    ]

    test_workbooks = {}

    for test in test_names:
        url, workbook_id, worksheet_id = setup_workbook(workbook_name=test)
        test_workbooks[test] = {
            "url": url,
            "workbook_id": workbook_id,
            "worksheet_id": worksheet_id,
        }

    return test_workbooks


@pytest.mark.system
def test_spc_accelerator_object_created_successfully(spc_accelerator_testing):
    test_workbooks = spc_accelerator_testing
    current_test_name = inspect.currentframe().f_code.co_name + " " + timestamp
    url = test_workbooks[current_test_name]["url"]
    workbook_id = test_workbooks[current_test_name]["workbook_id"]
    worksheet_id = test_workbooks[current_test_name]["worksheet_id"]
    spc_accelerator = SPCAccelerator(url, workbook_id, worksheet_id)

    # ipywidgets 7 needs separate ipydatetime import
    # ipywidgets 8 has ipydatetime included in ipywidgets
    if ipywidgets.__version__.startswith("7"):
        from ipydatetime import DatetimePicker
    else:
        from ipywidgets import DatetimePicker

    assert spc_accelerator.URL == url
    assert spc_accelerator.workbook_id == workbook_id
    assert spc_accelerator.worksheet_id == worksheet_id
    assert isinstance(spc_accelerator.app, v.App)
    assert isinstance(spc_accelerator.signal_list, list)
    assert isinstance(spc_accelerator.condition_list, list)
    assert isinstance(spc_accelerator.start_time, datetime)
    assert isinstance(spc_accelerator.end_time, datetime)
    assert isinstance(spc_accelerator.signals, pd.DataFrame)
    assert isinstance(spc_accelerator.conditions, pd.DataFrame)
    assert isinstance(spc_accelerator.input_signal, v.Select)
    assert isinstance(spc_accelerator.signal_interpolation, v.TextField)
    assert isinstance(spc_accelerator.interpolation_units, v.Select)
    assert isinstance(spc_accelerator.input_condition, v.Select)
    assert isinstance(spc_accelerator.capsule_property, v.Select)
    assert isinstance(spc_accelerator.start_select, DatetimePicker)
    assert isinstance(spc_accelerator.end_select, DatetimePicker)
    assert isinstance(spc_accelerator.apply_to_condition, v.Select)
    assert isinstance(spc_accelerator.control_chart, v.Checkbox)
    assert isinstance(spc_accelerator.we_runrules, v.Checkbox)
    assert isinstance(spc_accelerator.nelson_runrules, v.Checkbox)
    assert isinstance(spc_accelerator.histogram, v.Checkbox)
    assert isinstance(spc_accelerator.button, v.Btn)
    assert isinstance(spc_accelerator.workbook_button, v.Btn)
    assert isinstance(spc_accelerator.error, v.Alert)
    assert isinstance(spc_accelerator.success, v.Alert)


# Test for input_signal required and training windows is setup correctly
@pytest.mark.system
def test_missing_input_signal_training_window(spc_accelerator_testing):
    test_workbooks = spc_accelerator_testing
    current_test_name = inspect.currentframe().f_code.co_name + " " + timestamp
    url = test_workbooks[current_test_name]["url"]
    workbook_id = test_workbooks[current_test_name]["workbook_id"]
    worksheet_id = test_workbooks[current_test_name]["worksheet_id"]
    spc_accelerator = SPCAccelerator(url, workbook_id, worksheet_id)

    # Set initial value of self.success.value to True
    spc_accelerator.success.value = True

    # Call the input_validation method
    spc_accelerator.input_validation()

    # Check that self.success.value is True
    assert spc_accelerator.input_signal.error == True
    assert spc_accelerator.error.value == False


@pytest.mark.system
def test_create_control_chart_signal_only(spc_accelerator_testing):
    test_workbooks = spc_accelerator_testing
    current_test_name = inspect.currentframe().f_code.co_name + " " + timestamp
    url = test_workbooks[current_test_name]["url"]
    workbook_id = test_workbooks[current_test_name]["workbook_id"]
    worksheet_id = test_workbooks[current_test_name]["worksheet_id"]
    spc_accelerator = SPCAccelerator(url, workbook_id, worksheet_id)

    spc_accelerator.input_signal.v_model = ["Temperature"]

    # Call the input_validation method
    spc_accelerator.input_validation()

    # Check that success.value is now False
    assert spc_accelerator.input_signal.error == False
    assert spc_accelerator.error.value == False
    assert spc_accelerator.workbook_button.disabled == False


@pytest.mark.system
def test_create_control_chart_signal_condition(spc_accelerator_testing):
    test_workbooks = spc_accelerator_testing
    current_test_name = inspect.currentframe().f_code.co_name + " " + timestamp
    url = test_workbooks[current_test_name]["url"]
    workbook_id = test_workbooks[current_test_name]["workbook_id"]
    worksheet_id = test_workbooks[current_test_name]["worksheet_id"]
    spc_accelerator = SPCAccelerator(url, workbook_id, worksheet_id)

    spc_accelerator.input_signal.v_model = ["Temperature"]
    spc_accelerator.input_condition.v_model = "Temperature > 90"
    spc_accelerator.apply_to_condition.v_model = "Temperature > 90"

    # Call the input_validation method
    spc_accelerator.input_validation()

    # Check that success.value is now False
    assert spc_accelerator.input_signal.error == False
    assert spc_accelerator.error.value == False
    assert spc_accelerator.workbook_button.disabled == False


@pytest.mark.system
def test_create_control_chart_signal_condition(spc_accelerator_testing):
    test_workbooks = spc_accelerator_testing
    current_test_name = inspect.currentframe().f_code.co_name + " " + timestamp
    url = test_workbooks[current_test_name]["url"]
    workbook_id = test_workbooks[current_test_name]["workbook_id"]
    worksheet_id = test_workbooks[current_test_name]["worksheet_id"]
    spc_accelerator = SPCAccelerator(url, workbook_id, worksheet_id)

    spc_accelerator.input_signal.v_model = ["Temperature"]
    spc_accelerator.input_condition.v_model = "Temperature > 90"
    spc_accelerator.apply_to_condition.v_model = "Temperature > 90"

    # Call the input_validation method
    spc_accelerator.input_validation()

    # Check that success.value is now False
    assert spc_accelerator.input_signal.error == False
    assert spc_accelerator.error.value == False
    assert spc_accelerator.workbook_button.disabled == False


@pytest.mark.system
def test_create_control_chart_we_runrules(spc_accelerator_testing):
    test_workbooks = spc_accelerator_testing
    current_test_name = inspect.currentframe().f_code.co_name + " " + timestamp
    url = test_workbooks[current_test_name]["url"]
    workbook_id = test_workbooks[current_test_name]["workbook_id"]
    worksheet_id = test_workbooks[current_test_name]["worksheet_id"]
    spc_accelerator = SPCAccelerator(url, workbook_id, worksheet_id)

    spc_accelerator.input_signal.v_model = ["Temperature"]
    spc_accelerator.input_condition.v_model = "Temperature > 90"
    spc_accelerator.apply_to_condition.v_model = "Temperature > 90"
    spc_accelerator.we_runrules.v_model = True

    # Call the input_validation method
    spc_accelerator.input_validation()

    # Check that success.value is now False
    assert spc_accelerator.input_signal.error == False
    assert spc_accelerator.error.value == False
    assert spc_accelerator.workbook_button.disabled == False


@pytest.mark.system
def test_create_control_chart_nelson_runrules(spc_accelerator_testing):
    test_workbooks = spc_accelerator_testing
    current_test_name = inspect.currentframe().f_code.co_name + " " + timestamp
    url = test_workbooks[current_test_name]["url"]
    workbook_id = test_workbooks[current_test_name]["workbook_id"]
    worksheet_id = test_workbooks[current_test_name]["worksheet_id"]
    spc_accelerator = SPCAccelerator(url, workbook_id, worksheet_id)

    spc_accelerator.input_signal.v_model = ["Temperature"]
    spc_accelerator.input_condition.v_model = "Temperature > 90"
    spc_accelerator.apply_to_condition.v_model = "Temperature > 90"
    spc_accelerator.nelson_runrules.v_model = True

    # Call the input_validation method
    spc_accelerator.input_validation()

    # Check that success.value is now False
    assert spc_accelerator.input_signal.error == False
    assert spc_accelerator.error.value == False
    assert spc_accelerator.workbook_button.disabled == False


@pytest.mark.system
def test_create_control_chart_histogram(spc_accelerator_testing):
    test_workbooks = spc_accelerator_testing
    current_test_name = inspect.currentframe().f_code.co_name + " " + timestamp
    url = test_workbooks[current_test_name]["url"]
    workbook_id = test_workbooks[current_test_name]["workbook_id"]
    worksheet_id = test_workbooks[current_test_name]["worksheet_id"]
    spc_accelerator = SPCAccelerator(url, workbook_id, worksheet_id)

    spc_accelerator.input_signal.v_model = ["Temperature"]
    spc_accelerator.input_condition.v_model = "Temperature > 90"
    spc_accelerator.apply_to_condition.v_model = "Temperature > 90"
    spc_accelerator.histogram.v_model = True

    # Call the input_validation method
    spc_accelerator.input_validation()

    # Check that success.value is now False
    assert spc_accelerator.input_signal.error == False
    assert spc_accelerator.error.value == False
    assert spc_accelerator.workbook_button.disabled == False


@pytest.mark.system
def test_create_control_chart_capsule_prop(spc_accelerator_testing):
    test_workbooks = spc_accelerator_testing
    current_test_name = inspect.currentframe().f_code.co_name + " " + timestamp
    url = test_workbooks[current_test_name]["url"]
    workbook_id = test_workbooks[current_test_name]["workbook_id"]
    worksheet_id = test_workbooks[current_test_name]["worksheet_id"]
    spc_accelerator = SPCAccelerator(url, workbook_id, worksheet_id)

    spc_accelerator.input_signal.v_model = ["Temperature"]
    spc_accelerator.input_condition.v_model = "Temperature > 90"
    spc_accelerator.apply_to_condition.v_model = "Temperature > 90"
    spc_accelerator.capsule_property.v_model = "Date"

    # Call the input_validation method
    spc_accelerator.input_validation()

    # Check that success.value is now False
    assert spc_accelerator.input_signal.error == False
    assert spc_accelerator.error.value == False
    assert spc_accelerator.workbook_button.disabled == False


@pytest.mark.system
def test_create_control_chart_apply_condition(spc_accelerator_testing):
    test_workbooks = spc_accelerator_testing
    current_test_name = inspect.currentframe().f_code.co_name + " " + timestamp
    url = test_workbooks[current_test_name]["url"]
    workbook_id = test_workbooks[current_test_name]["workbook_id"]
    worksheet_id = test_workbooks[current_test_name]["worksheet_id"]
    spc_accelerator = SPCAccelerator(url, workbook_id, worksheet_id)

    spc_accelerator.input_signal.v_model = ["Temperature"]
    spc_accelerator.input_condition.v_model = "Temperature > 90"
    # spc_accelerator.capsule_property.v_model = 'Date'
    spc_accelerator.apply_to_condition.v_model = "Days"

    # Call the input_validation method
    spc_accelerator.input_validation()

    # Check that success.value is now False
    assert spc_accelerator.input_signal.error == False
    assert spc_accelerator.error.value == False
    assert spc_accelerator.workbook_button.disabled == False
