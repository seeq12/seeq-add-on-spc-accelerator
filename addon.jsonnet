function(suffix='')
  local add_on_identifier = 'com.seeq.addon.spc-accelerator';  // unique identifier for add-on. Follow form com.seeq.addon.[name]
  local add_on_name = 'SPC Accelerator';
  {
    local hyphen_suffix = if suffix == '' then '' else '-' + suffix,
    local underscore_suffix = if suffix == '' then '' else '_' + suffix,
    local name_suffix = if suffix == '' then '' else ' [' + suffix + ']',
    identifier: add_on_identifier + hyphen_suffix,
    name: add_on_name + name_suffix,
    artifactory_dir: std.asciiLower((std.strReplace(add_on_name, ' ', '_') + underscore_suffix)),  // used when deploying to artifactory
    description: |||
      Create Statistical Process Control (SPC) control charts and apply run rules

      This Add-on is maintained by a member of the Seeq Analytics Engineering team. Feature requests and bugs are handled through GitHub, please submit these requests as issues in the corresponding GitHub repository:

      https://github.com/seeq12/seeq-add-on-spc-accelerator/issues
    |||,
    version: '1.0.0',
    license: 'Apache 2.0',
    icon: 'fa-bullseye',
    maintainer: 'Seeq Corporation',  // set to Seeq Corporation for AE developed add-ons
    previews: [
      'docs/source/_static/preview.png',
    ],
    elements: [
      {
        name: $.name,  // the UI name should match the overall add-on name
        description: 'Create Statistical Process Control (SPC) control charts and apply run rules',
        local element_identifier = 'ui',  // identifier for the element, needs to be unique amonst the elements
        identifier: add_on_identifier + '.' + element_identifier + hyphen_suffix,
        type: 'AddOnTool',
        path: 'add-on-tool',
        notebook_file_path: 'SPC Accelerator.ipynb',
        extensions: [],
        configuration_schema: {
          type: 'object',
          properties: {
            display: {
              type: 'object',
              properties: {
                icon: { type: 'string', default: 'fa-bullseye' },
                linkType: { enum: ['window', 'tab', 'none'], default: 'window' },
                sortKey: { type: 'string', default: 'S' },
                windowDetails: { type: 'string', default: 'toolbar=0,location=0,scrollbars=1,statusbar=0,menubar=0,resizable=1,height=925,width=425' },
                reuseWindow: { type: 'boolean', default: true },
                includeWorkbookParameters: { type: 'boolean', default: true },
              },
              required: ['icon', 'linkType', 'sortKey', 'windowDetails', 'reuseWindow', 'includeWorkbookParameters'],
            },
            [if suffix != '' then 'project']: {  // project should only be included for dev versions
              type: 'object',
              required: ['suffix'],
              properties: {
                // these properties will be included in a configuration.json file in the add-on-tool project
                suffix: { type: 'string', default: suffix },
              },
            },
          },
          required: ['display'] + if suffix != '' then ['project'] else [],
        },
        configuration_filename: 'configuration',  // name of the file dropped in the add-on-tool project
        configuration_converter: 'json',  // options for ini, toml, json
      },
      {
        name: 'Nelson Run Rules',
        local element_identifier = 'nelson-run-rules',  // identifier for the element, needs to be unique amonst the elements
        identifier: add_on_identifier + '.' + element_identifier + hyphen_suffix,
        type: 'FormulaPackage',
        path: 'nelson-run-rules',
      },
      {
        name: 'Western Electric Run Rules',
        local element_identifier = 'western-electric-run-rules',  // identifier for the element, needs to be unique amonst the elements
        identifier: add_on_identifier + '.' + element_identifier + hyphen_suffix,
        type: 'FormulaPackage',
        path: 'western-electric-run-rules',
      },
    ],
  }
