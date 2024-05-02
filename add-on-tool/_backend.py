from seeq import spy
from seeq import sdk
import pandas as pd
import json
import re
import math
import os
from _templates import create_template, format_histogram_worksheet

# when deploying a test instance, need to append a suffix to the formula package names to prevent collisons
try:
    with open("configuration.json", "r") as f:
        configuration = json.load(f)
        ADD_ON_SUFFIX = configuration.get("suffix", "")
except:
    ADD_ON_SUFFIX = ""

workbooks_api = sdk.WorkbooksApi(spy.client)
formulaAPI = sdk.FormulasApi(spy.client)
itemsAPI = sdk.ItemsApi(spy.client)


def create_control_chart(*args):
    if len(args) == 1:
        instance = args[0]
        URL = instance.URL
        workbook_id = instance.workbook_id
        worksheet_id = instance.worksheet_id
        signal_list = instance.signal_list
        signals = instance.signals
        condition_list = instance.condition_list
        conditions = instance.conditions
        start_time = instance.start_time
        end_time = instance.end_time
        input_signal = instance.input_signal
        signal_interpolation = instance.signal_interpolation
        interpolation_units = instance.interpolation_units
        capsule_property = instance.capsule_property
        start_select = instance.start_select
        end_select = instance.end_select
        apply_to_condition = instance.apply_to_condition
        control_chart = instance.control_chart
        we_runrules = instance.we_runrules
        nelson_runrules = instance.nelson_runrules
        histogram = instance.histogram
        button = instance.button
        workbook_button = instance.workbook_button
        error = instance.error
        success = instance.success
        input_condition = instance.input_condition

    workbook_button.disabled = True
    button.disabled = True
    button.loading = True
    capsule_start = re.sub(" ", "T", str(start_select.value))
    capsule_end = re.sub(" ", "T", str(end_select.value))
    units_lookup_dict = {
        "second(s)": "s",
        "minute(s)": "min",
        "hour(s)": "h",
        "day(s)": "d",
    }
    unit_str = interpolation_units.v_model
    for word, unit in units_lookup_dict.items():
        unit_str = unit_str.replace(word, unit)
    interp_value = str(signal_interpolation.v_model) + unit_str
    num_completed = 0
    signals_completed = ""
    display_dict = {}
    histogram_dict = {}
    for signal_name in input_signal.v_model:
        # Create and push average and standard deviation formulas
        average_formula_string = create_mean_formula_string(
            capsule_start,
            capsule_end,
            input_condition,
            capsule_property,
            conditions,
            start_select,
            end_select,
        )
        stddev_formula_string = create_stddev_formula_string(average_formula_string)
        mean_stddev_signal_df = create_mean_and_stddev_signals(
            average_formula_string,
            stddev_formula_string,
            signal_name,
            input_condition,
            signals,
            conditions,
            apply_to_condition,
        )
        mean_stddev_push_df = push_signals(
            mean_stddev_signal_df, workbook_id, f"{signal_name} Control Chart"
        )

        # Create and push 1, 2, and 3 sigma limits
        limits_df = create_limit_signals(mean_stddev_push_df, signal_name)
        limits_push_df = push_signals(
            limits_df, workbook_id, f"{signal_name} Control Chart"
        )
        created_string = "Control Chart"
        control_chart_signal_list = [
            mean_stddev_push_df[
                mean_stddev_push_df["Name"] == f"{signal_name}: Mean"
            ].ID.iloc[0]
        ]
        control_chart_signal_list += limits_push_df.ID.to_list()
        control_chart_signal_list += [
            signals[signals["Name"] == signal_name].ID.iloc[0]
        ]
        if isinstance(input_condition.v_model, str):
            control_chart_signal_list += [
                conditions[conditions["Name"] == apply_to_condition.v_model].ID.iloc[0]
            ]
        display_dict[f"{signal_name} Control Chart"] = control_chart_signal_list

        # Create Western Electric Run Rules
        if we_runrules.v_model == True:
            western_electric_rules_df = western_electric_df(
                limits_push_df, mean_stddev_push_df, signal_name, interp_value, signals
            )
            western_electric_push_df = push_signals(
                western_electric_rules_df,
                workbook_id,
                f"{signal_name} Western Electric Run Rules",
            )
            if (nelson_runrules.v_model == True) or (histogram.v_model == True):
                created_string += ", Western Electric Run Rules, "
            else:
                created_string += " and Western Electric Run Rules"
            western_electric_signal_list = control_chart_signal_list.copy()
            western_electric_signal_list += western_electric_push_df.ID.to_list()
            display_dict[f"{signal_name} Western Electric Run Rules"] = (
                western_electric_signal_list
            )

        # Create Nelson Run Rules
        if nelson_runrules.v_model == True:
            nelson_rules_df = nelson_df(
                limits_push_df, mean_stddev_push_df, signal_name, interp_value, signals
            )
            nelson_push_df = push_signals(
                nelson_rules_df, workbook_id, f"{signal_name} Nelson Run Rules"
            )
            if histogram.v_model == True:
                created_string += "Nelson Run Rules, "
            else:
                created_string += " and Nelson Run Rules"
            nelson_signal_list = control_chart_signal_list.copy()
            nelson_signal_list += nelson_push_df.ID.to_list()
            display_dict[f"{signal_name} Nelson Run Rules"] = nelson_signal_list
        if num_completed == 0:
            signals_completed += signal_name
        else:
            signals_completed += ", " + signal_name

        # Create Histogram for Normality Test
        if histogram.v_model == True:
            if isinstance(input_condition.v_model, str):
                within_signal_df = within_condition_signal_df(
                    signal_name, input_condition, signals, conditions
                )
                within_signal_push_df = push_signals(
                    within_signal_df, workbook_id, f"{signal_name} Histogram"
                )
                histogram_id = create_histogram(
                    within_signal_push_df,
                    start_select.value.isoformat(),
                    end_select.value.isoformat(),
                    input_condition,
                    conditions,
                    workbook_id,
                    capsule_property,
                )
            else:
                histogram_id = create_histogram(
                    signals[signals["Name"] == signal_name],
                    start_select.value.isoformat(),
                    end_select.value.isoformat(),
                    input_condition,
                    conditions,
                    workbook_id,
                    capsule_property,
                )
            format_histogram_worksheet(histogram_id, signal_name, URL, workbook_id)
            histogram_dict[f"{signal_name} Histogram"] = histogram_id
            created_string += " and Histogram"
        num_completed += 1
        success.children = [
            f"{num_completed} of {len(input_signal.v_model)} signals completed. Created {created_string} for {signals_completed}."
        ]
        success.value = True

    # Edit the worksheet(s) display(s) to specify formatting
    success.children = [
        f"{num_completed} of {len(input_signal.v_model)} signals completed. Created {created_string} for {signal_name}. Formatting worksheets..."
    ]

    worksheet_data_dict = create_template(
        URL,
        display_dict,
        histogram,
        input_condition,
        start_select,
        end_select,
        workbook_button,
        workbook_id,
        histogram_dict,
    )

    success.children = [
        f"""{num_completed} of {len(input_signal.v_model)} signals completed. Created {created_string} for {signal_name}. 
        Formatting complete. Click link to be taken to the results."""
    ]

    workbook_button.disabled = False
    button.disabled = False
    button.loading = False

    return workbook_button, success, button


def set_apply_to_condition(apply_to_condition, input_condition):
    if not isinstance(apply_to_condition.v_model, str):
        apply_to_condition.v_model = input_condition.v_model


def disable_apply_to_condition(apply_to_condition, input_condition):
    if not isinstance(input_condition.v_model, str):
        apply_to_condition.disabled = True


def check_input_signal(input_signal):
    if len(input_signal.v_model) == 0:
        input_signal.error = True
        input_signal.error_messages = "This field is required."
    else:
        input_signal.error = False
        input_signal.error_messages = ""
    return input_signal


def check_training_window(end_select, start_select, error):
    if (end_select.value - start_select.value).total_seconds() < 0:
        error.value = True
    else:
        error.value = False
    return error


def create_mean_formula_string(
    capsule_start,
    capsule_end,
    input_condition,
    capsule_property,
    conditions,
    start_select,
    end_select,
):
    if isinstance(capsule_property.v_model, str):
        capsules = spy.pull(
            conditions[conditions["Name"] == input_condition.v_model],
            start=start_select.value,
            end=end_select.value,
            quiet=True,
        )
        unique_properties = capsules[capsule_property.v_model].unique().tolist()
        capsule_string = f"//Define the time period that contains all in control capsules\n$capsule = capsule('{capsule_start}', '{capsule_end}')"
        in_control_string = "\n \n//Narrow down data to when process is in control, use keep() to filter the condition by the specific grade code capsule property\n"
        unweighted_average_string = "\n \n//Create average based on the times the product is in control, use .toDiscrete to create an unweighted average\n"
        output_string = "\n \n//Create average for all grades in one signal using splice(), use keep() to filter the condition by the specific grade code capsule property\n//use within() to show only average only during the condition\n0"
        # iterate through each unique property value to add to the average formula
        for prop in unique_properties:
            if isinstance(prop, str) and prop and prop[0].isalpha():
                property_text = re.sub(r'\W+', '', prop)
                prop_match = "'" + prop + "'"
            else:
                property_text = "a" + re.sub(r'\W+', '', str(prop))
                prop_match = prop
            in_control_string += f"${property_text} = $applytocondition.keep('{capsule_property.v_model}', isMatch({prop_match})).intersect($inputcondition)\n"
            unweighted_average_string += f"${property_text}_average = $inputsignal.remove(not ${property_text}).toDiscrete().average($capsule)\n"
            output_string += f".splice(${property_text}_average, $applytocondition.keep('{capsule_property.v_model}', isMatch({prop_match})))\n"
        output_string += ".within($applytocondition)"
        average_formula_string = (
            capsule_string
            + in_control_string
            + unweighted_average_string
            + output_string
        )
    elif isinstance(input_condition.v_model, str):
        capsule_string = f"//Define the time period that contains all in control capsules\n$capsule = capsule('{capsule_start}', '{capsule_end}')"
        unweighted_average_string = "\n \n//Create average based on the times the product is in control, use .toDiscrete to create an unweighted average\n"
        unweighted_average_string += "$average = $inputsignal.remove(not $applytocondition.intersect($inputcondition)).toDiscrete().average($capsule).tosignal()"
        output_string = "\n \n//Create average using within() to show only average only during the condition\n"
        output_string += "$average.within($applytocondition)"
        average_formula_string = (
            capsule_string + unweighted_average_string + output_string
        )
    else:
        capsule_string = f"//Define the time period that contains all in control capsules\n$capsule = capsule('{capsule_start}', '{capsule_end}')"
        unweighted_average_string = "\n \n//Create average based on the times within the training window, use .toDiscrete to create an unweighted average\n"
        unweighted_average_string += (
            "$inputsignal.toDiscrete().average($capsule).tosignal()"
        )
        average_formula_string = capsule_string + unweighted_average_string
    return average_formula_string


def create_stddev_formula_string(average_formula_string):
    # standard deviation formula is the same as average formula, just replacing average with stddev
    stddev_formula_string = re.sub("average", "stddev", average_formula_string)
    return stddev_formula_string


def push_signals(push_df, workbook_id, worksheet_name):
    push_results = spy.push(
        metadata=push_df, workbook=workbook_id, worksheet=worksheet_name, quiet=True
    )
    return push_results


def create_mean_and_stddev_signals(
    average_formula_string,
    stddev_formula_string,
    signal_name,
    input_condition,
    signals,
    conditions,
    apply_to_condition,
):
    if isinstance(input_condition.v_model, str):
        mean_stddev_signal_df = pd.DataFrame(
            [
                {
                    "Name": f"{signal_name}: Mean",
                    "Type": "Signal",
                    "Formula": average_formula_string,
                    "Formula Parameters": {
                        "$inputcondition": conditions[
                            conditions["Name"] == input_condition.v_model
                        ],
                        "$inputsignal": signals[signals["Name"] == signal_name],
                        "$applytocondition": conditions[
                            conditions["Name"] == apply_to_condition.v_model
                        ],
                    },
                },
                {
                    "Name": f"{signal_name}: Standard Deviation",
                    "Type": "Signal",
                    "Formula": stddev_formula_string,
                    "Formula Parameters": {
                        "$inputcondition": conditions[
                            conditions["Name"] == input_condition.v_model
                        ],
                        "$inputsignal": signals[signals["Name"] == signal_name],
                        "$applytocondition": conditions[
                            conditions["Name"] == apply_to_condition.v_model
                        ],
                    },
                },
            ]
        )
    else:
        mean_stddev_signal_df = pd.DataFrame(
            [
                {
                    "Name": f"{signal_name}: Mean",
                    "Type": "Signal",
                    "Formula": average_formula_string,
                    "Formula Parameters": {
                        "$inputsignal": signals[signals["Name"] == signal_name]
                    },
                },
                {
                    "Name": f"{signal_name}: Standard Deviation",
                    "Type": "Signal",
                    "Formula": stddev_formula_string,
                    "Formula Parameters": {
                        "$inputsignal": signals[signals["Name"] == signal_name]
                    },
                },
            ]
        )
    return mean_stddev_signal_df


def create_limit_signals(mean_stddev_push_df, signal_name):
    limits_df = pd.DataFrame(
        [
            {
                "Name": f"{signal_name}: +1 Sigma",
                "Type": "Signal",
                "Formula": "$Mean + 1*$StandardDeviation",
                "Formula Parameters": {
                    "$Mean": mean_stddev_push_df[
                        mean_stddev_push_df["Name"] == f"{signal_name}: Mean"
                    ],
                    "$StandardDeviation": mean_stddev_push_df[
                        mean_stddev_push_df["Name"]
                        == f"{signal_name}: Standard Deviation"
                    ],
                },
            },
            {
                "Name": f"{signal_name}: -1 Sigma",
                "Type": "Signal",
                "Formula": "$Mean - 1*$StandardDeviation",
                "Formula Parameters": {
                    "$Mean": mean_stddev_push_df[
                        mean_stddev_push_df["Name"] == f"{signal_name}: Mean"
                    ],
                    "$StandardDeviation": mean_stddev_push_df[
                        mean_stddev_push_df["Name"]
                        == f"{signal_name}: Standard Deviation"
                    ],
                },
            },
            {
                "Name": f"{signal_name}: +2 Sigma",
                "Type": "Signal",
                "Formula": "$Mean + 2*$StandardDeviation",
                "Formula Parameters": {
                    "$Mean": mean_stddev_push_df[
                        mean_stddev_push_df["Name"] == f"{signal_name}: Mean"
                    ],
                    "$StandardDeviation": mean_stddev_push_df[
                        mean_stddev_push_df["Name"]
                        == f"{signal_name}: Standard Deviation"
                    ],
                },
            },
            {
                "Name": f"{signal_name}: -2 Sigma",
                "Type": "Signal",
                "Formula": "$Mean - 2*$StandardDeviation",
                "Formula Parameters": {
                    "$Mean": mean_stddev_push_df[
                        mean_stddev_push_df["Name"] == f"{signal_name}: Mean"
                    ],
                    "$StandardDeviation": mean_stddev_push_df[
                        mean_stddev_push_df["Name"]
                        == f"{signal_name}: Standard Deviation"
                    ],
                },
            },
            {
                "Name": f"{signal_name}: +3 Sigma",
                "Type": "Signal",
                "Formula": "$Mean + 3*$StandardDeviation",
                "Formula Parameters": {
                    "$Mean": mean_stddev_push_df[
                        mean_stddev_push_df["Name"] == f"{signal_name}: Mean"
                    ],
                    "$StandardDeviation": mean_stddev_push_df[
                        mean_stddev_push_df["Name"]
                        == f"{signal_name}: Standard Deviation"
                    ],
                },
            },
            {
                "Name": f"{signal_name}: -3 Sigma",
                "Type": "Signal",
                "Formula": "$Mean - 3*$StandardDeviation",
                "Formula Parameters": {
                    "$Mean": mean_stddev_push_df[
                        mean_stddev_push_df["Name"] == f"{signal_name}: Mean"
                    ],
                    "$StandardDeviation": mean_stddev_push_df[
                        mean_stddev_push_df["Name"]
                        == f"{signal_name}: Standard Deviation"
                    ],
                },
            },
        ]
    )
    return limits_df


def western_electric_df(
    limits_push_df, mean_stddev_push_df, signal_name, interp_value, signals
):
    western_electric_rules_df = pd.DataFrame(
        [
            {
                "Name": f"{signal_name}: Western Electric Run Rule 1",
                "Type": "Condition",
                "Formula": f"$inputsignal.WesternElectricRunRules{ADD_ON_SUFFIX}_RunRule1($minus3sd, $plus3sd)",
                "Formula Parameters": {
                    "$inputsignal": signals[signals["Name"] == signal_name],
                    "$minus3sd": limits_push_df[
                        limits_push_df["Name"] == f"{signal_name}: -3 Sigma"
                    ],
                    "$plus3sd": limits_push_df[
                        limits_push_df["Name"] == f"{signal_name}: +3 Sigma"
                    ],
                },
            },
            {
                "Name": f"{signal_name}: Western Electric Run Rule 2",
                "Type": "Condition",
                "Formula": f"$inputsignal.WesternElectricRunRules{ADD_ON_SUFFIX}_RunRule2($minus2sd, $plus2sd, "
                + interp_value
                + ")",
                "Formula Parameters": {
                    "$inputsignal": signals[signals["Name"] == signal_name],
                    "$minus2sd": limits_push_df[
                        limits_push_df["Name"] == f"{signal_name}: -2 Sigma"
                    ],
                    "$plus2sd": limits_push_df[
                        limits_push_df["Name"] == f"{signal_name}: +2 Sigma"
                    ],
                },
            },
            {
                "Name": f"{signal_name}: Western Electric Run Rule 3",
                "Type": "Condition",
                "Formula": f"$inputsignal.WesternElectricRunRules{ADD_ON_SUFFIX}_RunRule3($minus1sd, $plus1sd, "
                + interp_value
                + ")",
                "Formula Parameters": {
                    "$inputsignal": signals[signals["Name"] == signal_name],
                    "$minus1sd": limits_push_df[
                        limits_push_df["Name"] == f"{signal_name}: -1 Sigma"
                    ],
                    "$plus1sd": limits_push_df[
                        limits_push_df["Name"] == f"{signal_name}: +1 Sigma"
                    ],
                },
            },
            {
                "Name": f"{signal_name}: Western Electric Run Rule 4",
                "Type": "Condition",
                "Formula": f"$inputsignal.WesternElectricRunRules{ADD_ON_SUFFIX}_RunRule4($mean, "
                + interp_value
                + ")",
                "Formula Parameters": {
                    "$inputsignal": signals[signals["Name"] == signal_name],
                    "$mean": mean_stddev_push_df[
                        mean_stddev_push_df["Name"] == f"{signal_name}: Mean"
                    ],
                },
            },
        ]
    )
    return western_electric_rules_df


def nelson_df(limits_push_df, mean_stddev_push_df, signal_name, interp_value, signals):
    nelson_rules_df = pd.DataFrame(
        [
            {
                "Name": f"{signal_name}: Nelson Run Rule 1",
                "Type": "Condition",
                "Formula": f"$inputsignal.NelsonRunRules{ADD_ON_SUFFIX}_RunRule1($minus3sd, $plus3sd)",
                "Formula Parameters": {
                    "$inputsignal": signals[signals["Name"] == signal_name],
                    "$minus3sd": limits_push_df[
                        limits_push_df["Name"] == f"{signal_name}: -3 Sigma"
                    ],
                    "$plus3sd": limits_push_df[
                        limits_push_df["Name"] == f"{signal_name}: +3 Sigma"
                    ],
                },
            },
            {
                "Name": f"{signal_name}: Nelson Run Rule 2",
                "Type": "Condition",
                "Formula": f"$inputsignal.NelsonRunRules{ADD_ON_SUFFIX}_RunRule2($mean, "
                + interp_value
                + ")",
                "Formula Parameters": {
                    "$inputsignal": signals[signals["Name"] == signal_name],
                    "$mean": mean_stddev_push_df[
                        mean_stddev_push_df["Name"] == f"{signal_name}: Mean"
                    ],
                },
            },
            {
                "Name": f"{signal_name}: Nelson Run Rule 3",
                "Type": "Condition",
                "Formula": f"$inputsignal.NelsonRunRules{ADD_ON_SUFFIX}_RunRule3("
                + interp_value
                + ")",
                "Formula Parameters": {
                    "$inputsignal": signals[signals["Name"] == signal_name]
                },
            },
            {
                "Name": f"{signal_name}: Nelson Run Rule 4",
                "Type": "Condition",
                "Formula": f"$inputsignal.NelsonRunRules{ADD_ON_SUFFIX}_RunRule4("
                + interp_value
                + ")",
                "Formula Parameters": {
                    "$inputsignal": signals[signals["Name"] == signal_name]
                },
            },
            {
                "Name": f"{signal_name}: Nelson Run Rule 5",
                "Type": "Condition",
                "Formula": f"$inputsignal.NelsonRunRules{ADD_ON_SUFFIX}_RunRule5($minus2sd, $plus2sd, "
                + interp_value
                + ")",
                "Formula Parameters": {
                    "$inputsignal": signals[signals["Name"] == signal_name],
                    "$minus2sd": limits_push_df[
                        limits_push_df["Name"] == f"{signal_name}: -2 Sigma"
                    ],
                    "$plus2sd": limits_push_df[
                        limits_push_df["Name"] == f"{signal_name}: +2 Sigma"
                    ],
                },
            },
            {
                "Name": f"{signal_name}: Nelson Run Rule 6",
                "Type": "Condition",
                "Formula": f"$inputsignal.NelsonRunRules{ADD_ON_SUFFIX}_RunRule6($minus1sd, $plus1sd, "
                + interp_value
                + ")",
                "Formula Parameters": {
                    "$inputsignal": signals[signals["Name"] == signal_name],
                    "$minus1sd": limits_push_df[
                        limits_push_df["Name"] == f"{signal_name}: -1 Sigma"
                    ],
                    "$plus1sd": limits_push_df[
                        limits_push_df["Name"] == f"{signal_name}: +1 Sigma"
                    ],
                },
            },
            {
                "Name": f"{signal_name}: Nelson Run Rule 7",
                "Type": "Condition",
                "Formula": f"$inputsignal.NelsonRunRules{ADD_ON_SUFFIX}_RunRule7($minus1sd, $plus1sd, "
                + interp_value
                + ")",
                "Formula Parameters": {
                    "$inputsignal": signals[signals["Name"] == signal_name],
                    "$minus1sd": limits_push_df[
                        limits_push_df["Name"] == f"{signal_name}: -1 Sigma"
                    ],
                    "$plus1sd": limits_push_df[
                        limits_push_df["Name"] == f"{signal_name}: +1 Sigma"
                    ],
                },
            },
            {
                "Name": f"{signal_name}: Nelson Run Rule 8",
                "Type": "Condition",
                "Formula": f"$inputsignal.NelsonRunRules{ADD_ON_SUFFIX}_RunRule8($minus1sd, $plus1sd, "
                + interp_value
                + ")",
                "Formula Parameters": {
                    "$inputsignal": signals[signals["Name"] == signal_name],
                    "$minus1sd": limits_push_df[
                        limits_push_df["Name"] == f"{signal_name}: -1 Sigma"
                    ],
                    "$plus1sd": limits_push_df[
                        limits_push_df["Name"] == f"{signal_name}: +1 Sigma"
                    ],
                },
            },
        ]
    )
    return nelson_rules_df


def within_condition_signal_df(signal_name, input_condition, signals, conditions):
    within_signal_df = pd.DataFrame(
        [
            {
                "Name": f"{signal_name}: Within Condition",
                "Type": "Signal",
                "Formula": "$inputsignal.remove(not $inputcondition)",
                "Formula Parameters": {
                    "$inputsignal": signals[signals["Name"] == signal_name],
                    "$inputcondition": conditions[
                        conditions["Name"] == input_condition.v_model
                    ],
                },
            }
        ]
    )
    return within_signal_df


def create_histogram(
    signal_df,
    start_time,
    end_time,
    input_condition,
    conditions,
    workbook_id,
    capsule_property,
):
    formulaAPI = sdk.FormulasApi(spy.client)
    itemsAPI = sdk.ItemsApi(spy.client)

    data = spy.pull(signal_df, grid=None, quiet=True, start=start_time, end=end_time)
    signal_name = signal_df["Name"].iloc[0]
    matching_columns = [col for col in data.columns if signal_name in col]
    if matching_columns:
        if isinstance(capsule_property.v_model, str):
            column_name = matching_columns[0]
            max_value = data[column_name].mean() + 4 * data[column_name].std()
            min_value = data[column_name].mean() - 4 * data[column_name].std()
            number_of_bins = 2 * math.ceil(
                (1 + 3.322 * math.log10(data[column_name].count()))
            )
            fxn_input_step1 = sdk.FunctionInputV1(
                name=f"{signal_name} Histogram",
                scoped_to=workbook_id,
                type="Chart",
                formula='conditionTable($condition1.toGroup($viewCapsule, CapsuleBoundary.Intersect), "'
                + capsule_property.v_model
                + '", $yValueSignal2.toStates(capsule('
                + str(min_value)
                + ", "
                + str(max_value)
                + ").partition("
                + str((max_value - min_value) / number_of_bins)
                + ')).toCondition("yValueCol2").toGroup($viewCapsule, CapsuleBoundary.Intersect), "yValueCol2").addStatColumn("signalToAggregate", $signalToAggregate, count())',
                parameters=[
                    sdk.FormulaParameterInputV1(
                        name="condition1",
                        id=conditions[conditions["Name"] == input_condition.v_model][
                            "ID"
                        ].iloc[0],
                    ),
                    sdk.FormulaParameterInputV1(
                        name="yValueSignal2", id=signal_df["ID"].iloc[0]
                    ),
                    sdk.FormulaParameterInputV1(
                        name="signalToAggregate", id=signal_df["ID"].iloc[0]
                    ),
                    sdk.FormulaParameterInputV1(
                        unbound=True,
                        name="viewCapsule",
                        formula='capsule("'
                        + str(start_time)
                        + '", "'
                        + str(end_time)
                        + '")',
                    ),
                ],
            )
            step1 = formulaAPI.create_function(body=fxn_input_step1)
            # Setting UIConfig property to mimic Histogram Tool UI
            step2 = itemsAPI.set_property(
                property_name="UIConfig",
                id=step1.id,
                body=sdk.PropertyInputV1(
                    value='{"type":"aggregation-bins-table","advancedParametersCollapsed":true,"mode":"by_y_value","includeEmptyBuckets":false,"yValueSignal1":"","stat":{"key":"count","timeUnits":"s","percentile":null},"aggregationConfigs":[{"id":1,"mode":"by_condition","capsuleMode":"intersect","yValueBinMode":"number","valid":true,"yValueBinMin":'
                    + str(min_value)
                    + ',"yValueBinMax":'
                    + str(max_value)
                    + ',"numberOfBins":"'
                    + str(number_of_bins)
                    + '","conditionProperty":"'
                    + capsule_property.v_model
                    + '"},{"id":2,"mode":"by_y_value","capsuleMode":"intersect","yValueBinMode":"number","valid":true,"yValueBinMin":'
                    + str(min_value)
                    + ',"yValueBinMax":'
                    + str(max_value)
                    + ',"numberOfBins":"'
                    + str(number_of_bins)
                    + '","conditionProperty":"'
                    + capsule_property.v_model
                    + '"}]}'
                ),
            )
            # Running of histogram function to actually create the histogram
            step3 = formulaAPI.run_formula(
                function=step1.id,
                fragments=[
                    'viewCapsule=capsule("'
                    + str(start_time)
                    + '","'
                    + str(end_time)
                    + '")'
                ],
            )
        else:
            column_name = matching_columns[0]
            max_value = data[column_name].mean() + 4 * data[column_name].std()
            min_value = data[column_name].mean() - 4 * data[column_name].std()
            number_of_bins = math.ceil(
                (1 + 3.322 * math.log10(data[column_name].count()))
            )
            fxn_input_step1 = sdk.FunctionInputV1(
                name=f"{signal_name} Histogram",
                scoped_to=workbook_id,
                type="Chart",
                formula="conditionTable($yValueSignal1.toStates(capsule("
                + str(min_value)
                + ", "
                + str(max_value)
                + ").partition("
                + str((max_value - min_value) / number_of_bins)
                + ')).toCondition("yValueCol1").toGroup($viewCapsule, CapsuleBoundary.Intersect), "yValueCol1", capsule('
                + str(min_value)
                + ", "
                + str(max_value)
                + ").partition("
                + str((max_value - min_value) / number_of_bins)
                + ').property("value")).addStatColumn("signalToAggregate", $signalToAggregate, count())',
                parameters=[
                    sdk.FormulaParameterInputV1(
                        name="yValueSignal1", id=signal_df["ID"].iloc[0]
                    ),
                    sdk.FormulaParameterInputV1(
                        name="signalToAggregate", id=signal_df["ID"].iloc[0]
                    ),
                    sdk.FormulaParameterInputV1(
                        unbound=True,
                        name="viewCapsule",
                        formula='capsule("'
                        + str(start_time)
                        + '", "'
                        + str(end_time)
                        + '")',
                    ),
                ],
            )
            step1 = formulaAPI.create_function(body=fxn_input_step1)
            # Setting UIConfig property to mimic Histogram Tool UI
            step2 = itemsAPI.set_property(
                property_name="UIConfig",
                id=step1.id,
                body=sdk.PropertyInputV1(
                    value='{"type":"aggregation-bins-table","advancedParametersCollapsed":true,"mode":"by_y_value","includeEmptyBuckets":false,"yValueSignal1":"","stat":{"key":"count","timeUnits":"s","percentile":null},"aggregationConfigs":[{"id":1,"mode":"by_y_value","capsuleMode":"intersect","yValueBinMode":"number","valid":true,"yValueBinMin":'
                    + str(min_value)
                    + ',"yValueBinMax":'
                    + str(max_value)
                    + ',"numberOfBins":"'
                    + str(number_of_bins)
                    + '"}]}'
                ),
            )
        # Running of histogram function to actually create the histogram
        step3 = formulaAPI.run_formula(
            function=step1.id,
            fragments=[f'viewCapsule=capsule("{start_time}","{end_time}")'],
        )
    else:
        print(f"No column found in data matching '{signal_name}'.")
    return step1.id
