# User Guide


## Overview

The SPC Accelerator Add-on enables users to quickly and easily build SPC charts with Western Electric or Nelson Run Rule Conditions. 

The SPC Chart created with the Add-on is a simple implementation of an Individuals Chart, or I-Chart in Seeq, using the standard deviation (not the average of moving range) to construct the +/- sigma limits.

<center>
<img src="_static/preview.png" width="400px">
</center>

## Installation

The **SPC Accelerator** Add-on can be installed via [Add-on Manager](https://support.seeq.com/kb/latest/cloud/the-add-on-manager) by a Seeq administrator. Once the **SPC Accelerator** Add-on has been installed, it will be available for all users given access. If the **SPC Accelerator** Add-on does not appear in the Add-on Manager, contact your Seeq account team.

```{attention} If a version of SPC Accelerator was installed manually prior to Add-on Manager, we recommend uninstalling this copy using the Add-on Manager prior to installing the SPC Accelerator.
```

## Usage

1. Identify the Control Chart input signal and add to the worksheet trend. (Optional) Create conditions or conditions with properties to use as inputs to the SPC Accelerator Add-on Tool.
2. Open the SPC Accelerator Add-on Tool.
3. Select the input signal. 
4. Define the maximum signal interpolation. The default is 40 hours.
5. Select the Training Window and Conditions Filters. The combination used is dependent on the specific use case. Here are a couple of variations: 
    - **Choose only a Training Window.** This will calculate control limits based on the signal data within the training window
    - **Choose a Training Window and a Condition Filter.** This will calculate the control limits based on the the data within the condition that is within the training window. The condition used for the Condition Filter and the Apply To Condition can be the same condition or different conditions.
    - **Choose a Training Window and a Condition Filter with capsule properties.** This will calculate the control limits based on the the data within the condition that is within the training window, and it will create unique limits based on the unique property. For example, if there are multiple grade codes requiring separate control limits for the input signal, a condition with properties specifying the grade code can be used as an input to the SPC Accelerator. To input a condition with properties, use the Optional fields (Condition Filter and Spearate By Capsule Property), inputting the Condition Filter and the capsule property used to separate the data. Then, input a Training Window, when using properties, make sure the Training Window includes capsules from all desired properteis. The condition used for the Condition Filter and the Apply To Condition can be the same condition or different conditions, however, if capsule properties are used, the capsule properties must match to apply control limits correctly.
6. If a Condition Filter was chosen, choose the 'Apply to Condition.' This may be the same condition selected above, or a different condition.
7. Select the additional desired outputs: Control Chart, Western Electric Run Rules, Nelson Run Rules, Histogram Normality Check.

### SPC Accelerator Output

Once all of the selections are made and the add-on is executed, it will create new worksheets for each signal and output selection. For example, if an input signal and Control Chart and Nelson Run Rules are selected, a worksheet will be created for the control chart, containing a control chart, and a worksheet will be created for the Neson Run Rules, containing a control and the Nelson Run Rules conditions. 

### Supplemental Run Rules Information

See the table for information on the run rule conditions created using the SPC Accelerator Add-on.

<table width=100%>
    <thead>
    <tr>
        <td align="center"><b>Run Rule Description</b></td>
        <td align="center"><b>Nelson Run</b></td>
        <td align="center"><b>Western Electric</b></td>
        <td align="center"><b>Seeq Example</b></td>
    </tr>
    </thead>
    <tbody>
    <tr>
        <td>Any single data point falls outside the 3σ-limit from the centerline.</td>
        <td>Rule 1</td>
        <td>Rule 1</td>
        <td><img src="_static/run_rules/rule1.png"></td>
    </tr>
    <tr>
        <td>NINE consecutive points fall on the same side of the centerline (in zone C or beyond).</td>
        <td>Rule 2</td>
        <td>Rule 4</td>
        <td><img src="_static/run_rules/rule2.png"></td>
    </tr>
    <tr>
        <td>Six (or more) points in a row are continually increasing (or decreasing).</td>
        <td>Rule 3</td>
        <td></td>
        <td><img src="_static/run_rules/rule3.png"></td>
    </tr>
    <tr>
        <td>Fourteen (or more) points in a row alternate in direction, increasing then decreasing.</td>
        <td>Rule 4</td>
        <td></td>
        <td><img src="_static/run_rules/rule4.png"></td>
    </tr>
    <tr>
        <td>Two out of three consecutive points fall beyond the 2σ-limit (in zone A or beyond), on the same side of the centerline</td>
        <td>Rule 5</td>
        <td>Rule 2</td>
        <td><img src="_static/run_rules/rule5.png"></td>
    </tr>
    <tr>
        <td>Four out of five consecutive points fall beyond the 1σ-limit (in zone B or beyond), on the same side of the centerline</td>
        <td>Rule 6</td>
        <td>Rule 3</td>
        <td><img src="_static/run_rules/rule6-1.png"><img src="_static/run_rules/rule6-2.png"></td>
    </tr>
    <tr>
        <td>Fifteen points in a row are all within 1 standard deviation of the mean on either side of the mean.</td>
        <td>Rule 7</td>
        <td></td>
        <td><img src="_static/run_rules/rule7.png"></td>
    </tr>
    <tr>
        <td>Eight points in a row exist, but none within 1 standard deviation of the mean, and the points are in both directions from the mean.</td>
        <td>Rule 8</td>
        <td></td>
        <td><img src="_static/run_rules/rule8.png"></td>
    </tr>
    </tbody>
</table>


