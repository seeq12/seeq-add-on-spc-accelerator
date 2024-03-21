function(suffix='')
  local add_on_identifier = 'com.seeq.addon.spc-accelerator';  // unique identifier for add-on. Follow form com.seeq.addon.[name]
  {
    local hyphen_suffix = if suffix == '' then '' else '-' + suffix,
    local name_suffix = if suffix == '' then '' else ' [' + suffix + ']',
    identifier: add_on_identifier + hyphen_suffix,
    name: 'SPC Accelerator' + name_suffix,
    description: 'DESCRIPTION HERE',  // this will show on the add-on manager
    version: '0.1.0',
    license: 'Apache 2.0',
    icon: 'fa fa-wrench',
    maintainer: 'Seeq Corporation',  // set to Seeq Corporation for AE developed add-ons
    previews: [
      'docs/source/_static/preview.png',
    ],
    elements: [
      {
        name: $.name,  // the UI name should match the overall add-on name
        description: $.description,
        local element_identifier = 'ui',  // identifier for the element, needs to be unique amonst the elements
        identifier: add_on_identifier + '.' + element_identifier + hyphen_suffix,
        type: 'AddOnTool',
        path: 'add-on-tool',
        notebook_file_path: 'SPC Accelerator.ipynb',
        resource_size: 'GP_S',
        extensions: [],
        configuration_schema: {
          type: 'object',
          properties: {
            database: {
              type: 'object',
              properties: {
                host: {
                  type: 'string',
                  default: 'yourAmazingHostname',
                },
                port: {
                  type: 'string',
                  default: '5432',
                },
                username: {
                  type: 'string',
                  default: 'yourCoolUsername',
                },
                password: {
                  type: 'string',
                  default: 'yourSecretPassword',
                },
                database: {
                  type: 'string',
                  default: 'yourAwesomeDatabase',
                },
              },
              required: [
                'host',
                'port',
                'username',
                'password',
                'database',
              ],
            },
            display: {
              type: 'object',
              properties: {
                icon: { type: 'string', default: 'fa fa-arrows-h' },
                linkType: { enum: ['window', 'tab', 'none'], default: 'window' },
                sortKey: { type: 'string', default: 'S' },
                windowDetails: { type: 'string', default: 'toolbar=0,location=0,scrollbars=1,statusbar=0,menubar=0,resizable=1,height=700,width=600' },
                reuseWindow: { type: 'boolean', default: true },
                includeWorkbookParameters: { type: 'boolean', default: true },
              },
              required: ['icon', 'linkType', 'sortKey', 'windowDetails', 'reuseWindow', 'includeWorkbookParameters'],
            },
            project: { type: 'object', properties: {} },
          },
          required: ['display', 'database'],
        },
        // configuration_filename: 'configuration',
        // configuration_converter: 'ini',
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
