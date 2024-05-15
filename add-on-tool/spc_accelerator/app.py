from spc_accelerator.utils import pull_worksheet_data
from spc_accelerator.frontend import frontend
from spc_accelerator.backend import *
import ipywidgets as ipw
import ipyvuetify as v
from IPython.display import display


class SPCAccelerator:
    DOCS_URL = "https://seeq12.github.io/seeq-add-on-spc-accelerator/user_guide.html"
    ADDITIONAL_CSS = """
    .jp-Notebook {
        padding: 0px !important;
    }

    .v-application .primary--text {
        color: var(--dark-primary-analysis) !important;
        caret-color: var(--dark-primary-analysis) !important;
    }

    .vuetify-styles .v-label {
        font-size: 14px;
    }

    .vuetify-styles .v-input {
        font-size: 14px;
    }

    .vuetify-styles .v-application {
        font-family: 'Source Sans Pro','Helvetica Neue',Helvetica,Arial,sans-serif;
        font-size: 14px;
    }

    .vuetify-styles .v-input--selection-controls {
        margin-top: 0px;
        padding-top: 0px;
    }

    .execute {
        background-color: var(--dark-primary-analysis) !important;
        border-color: var(--dark-primary-analysis) !important;
        color: white !important;
        font-weight: normal !important;
        text-transform: unset !important;
        width: 125px;
    }
    
    .execute-container {
        justify-content: center;
    }
    """

    def __init__(self, URL, workbook_id, worksheet_id):
        self.URL = URL
        self.workbook_id = workbook_id
        self.worksheet_id = worksheet_id
        self.app = v.App(id="SPC Accelerator")
        self.output_results = ipw.Output
        (
            self.signal_list,
            self.condition_list,
            self.start_time,
            self.end_time,
            self.signals,
            self.conditions,
        ) = pull_worksheet_data(self.URL, self.workbook_id, self.worksheet_id)

        (
            self.input_signal,
            self.signal_interpolation,
            self.interpolation_units,
            self.input_condition,
            self.capsule_property,
            self.start_select,
            self.end_select,
            self.apply_to_condition,
            self.control_chart,
            self.we_runrules,
            self.nelson_runrules,
            self.histogram,
            self.button,
            self.workbook_button,
            self.error,
            self.success,
        ) = frontend(
            self.signal_list, self.condition_list, self.start_time, self.end_time
        )
        self.button.on_event(
            "click", lambda widget, event, data: self.input_validation()
        )
        self.input_condition.on_event(
            "change", lambda widget, event, data: self.check_properties()
        )

    def input_validation(self):
        self.success.value = False
        self.input_signal = check_input_signal(self.input_signal)
        self.error = check_training_window(
            self.end_select, self.start_select, self.error
        )

        if (self.input_signal.error == False) and (self.error.value == False):
            self.workbook_button, self.success, self.button = create_control_chart(self)

    def check_properties(self):
        "Adding single line doctsring"
        if isinstance(self.input_condition.v_model, str):
            self.apply_to_condition.disabled = False
            capsules = spy.pull(
                self.conditions[
                    self.conditions["Name"] == self.input_condition.v_model
                ],
                start=self.start_select.value,
                end=self.end_select.value,
                quiet=True,
            )
            property_list = capsules.columns.to_list()
            property_list = [s for s in property_list if s != "Condition"]
            property_list = [s for s in property_list if s != "Capsule Start"]
            property_list = [s for s in property_list if s != "Capsule End"]
            property_list = [s for s in property_list if s != "Capsule Is Uncertain"]
            self.capsule_property.v_model = property_list
            self.capsule_property.items = property_list
            set_apply_to_condition(self.apply_to_condition, self.input_condition)
        else:
            disable_apply_to_condition(self.apply_to_condition, self.input_condition)

    def display_error_widget(self, error_message):
        error_widget = ipw.HBox(
            [
                ipw.HTML(
                    value=f"""<font size='+0'><font color='red'><b>Error: {error_message}</b></font color></font size>"""
                )
            ]
        )
        display(error_widget)

    def run(self):
        display(
            v.App(
                children=[
                    v.Html(
                        tag="style",
                        children=[SPCAccelerator.ADDITIONAL_CSS],
                    ),
                    v.AppBar(
                        children=[
                            v.ToolbarTitle(children=["SPC Accelerator"]),
                            v.Spacer(),
                            v.Btn(
                                icon=True,
                                children=[v.Icon(children=["fa-question-circle"])],
                                href=SPCAccelerator.DOCS_URL,
                                target="_blank",
                            ),
                        ],
                        color="#007960",
                        dark=True,
                        dense=True,
                    ),
                    v.Html(
                        tag="div",
                        class_="d-flex flex-column pl-3 pr-3",
                        children=[
                            self.input_signal,
                            v.Html(
                                tag="div",
                                class_="d-flex flex-row",
                                children=[
                                    self.signal_interpolation,
                                    self.interpolation_units,
                                ],
                            ),
                            self.input_condition,
                            self.capsule_property,
                            v.Html(
                                tag="div",
                                children=["Training Window:"],
                            ),
                            self.start_select,
                            self.end_select,
                            self.apply_to_condition,
                            v.Html(
                                tag="div",
                                class_="pb-4",
                                children=["Desired Outputs:"],
                            ),
                            v.Html(
                                tag="div",
                                class_="d-flex flex-column ml-4",
                                children=[
                                    self.control_chart,
                                    self.we_runrules,
                                    self.nelson_runrules,
                                    self.histogram,
                                ],
                            ),
                            v.Html(
                                tag="div",
                                class_="d-flex flex-row execute-container",
                                children=[
                                    self.button,
                                    self.workbook_button,
                                ],
                            ),
                            self.error,
                            self.success,
                        ],
                    ),
                ],
            )
        )
