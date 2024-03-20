import ipyvuetify as v
import ipydatetime


def frontend(signal_list, condition_list, start_time, end_time):
    property_list = []
    input_signal = v.Select(
        v_model=[],
        items=signal_list,
        multiple=True,
        label="Input Signal",
        style_="width: 400px",
        no_data_text="No signals found on worksheet",
    )
    signal_interpolation = v.TextField(
        v_model=40,
        type="number",
        label="Maximum Signal Interpolation",
        style_="width: 200px",
    )
    interpolation_units = v.Select(
        items=["second(s)", "minute(s)", "hour(s)", "day(s)"],
        v_model="hour(s)",
        style_="width: 200px",
    )

    input_condition = v.Select(
        v_model=condition_list,
        items=condition_list,
        label="(Optional) Condition Filter",
        clearable=True,
        style_="width: 400px",
        no_data_text="No conditions found on worksheet",
    )
    capsule_property = v.Select(
        v_model=property_list,
        items=property_list,
        label="(Optional) Separate By Capsule Property",
        clearable=True,
        style_="width: 400px",
        no_data_text="No properties found on condition",
    )

    start_select = ipydatetime.DatetimePicker(
        description="Start Time: ", value=start_time
    )
    end_select = ipydatetime.DatetimePicker(description="End Time: ", value=end_time)

    apply_to_condition = v.Select(
        v_model=condition_list,
        items=condition_list,
        label="Apply to Condition",
        disabled=True,
        style_="width: 400px",
        no_data_text="No conditions found on worksheet",
    )

    control_chart = v.Checkbox(v_model=True, readonly=True, label="Control Chart")
    we_runrules = v.Checkbox(v_model=False, label="Western Electric Run Rules")
    nelson_runrules = v.Checkbox(v_model=False, label="Nelson Run Rules")
    histogram = v.Checkbox(v_model=False, label="Histogram Normality Check")

    button = v.Btn(children=["Execute"], color="success", loading=False, width="200px")
    workbook_button = v.Btn(
        children=[v.Icon(children=["mdi-open-in-new"])],
        color="primary",
        target="_blank",
        disabled=True,
    )
    error = v.Alert(
        type="error",
        dense=True,
        value=False,
        children=["Training Window: End time must be after start time."],
    )
    success = v.Alert(type="success", dense=True, value=False, children=[])

    return (
        input_signal,
        signal_interpolation,
        interpolation_units,
        input_condition,
        capsule_property,
        start_select,
        end_select,
        apply_to_condition,
        control_chart,
        we_runrules,
        nelson_runrules,
        histogram,
        button,
        workbook_button,
        error,
        success,
    )
