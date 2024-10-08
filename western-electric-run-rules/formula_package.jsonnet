function(suffix='')
  {
    formulaPackage: {
      name: 'WesternElectricRunRules' + suffix,
      creatorName: 'Christopher Harp',
      creatorContactInfo: 'christopher.harp@seeq.com',
    },
    functions: [
      {
        name: 'RunRule1',
        id: $.formulaPackage.name + self.name,
        description: '<p>Western Electric Run Rule One. \n This function creates a condition when any single data point falls outside the control limits from the centerline (i.e., any point that falls outside Zone A, beyond either the upper or lower control limit).</p>',
        formula: '    //Convert to a step signal\n    $signalStep = $signal.toStep()\n\n    //Find when one data point goes outside the +3 Standard Deviations ($plus3sd) or -3 Standard Deviations ($minus3sd) limits\n    ($signalStep < $minus3sd or $signalStep > $plus3sd)\n  ',
        type: 'UserDefinedFormulaFunction',
        parameters: [
          {
            unbound: true,
            name: 'signal',
            formula: '1.toSignal()',
          },
          {
            unbound: true,
            name: 'minus3sd',
            formula: '1.toSignal()',
          },
          {
            unbound: true,
            name: 'plus3sd',
            formula: '1.toSignal()',
          },
        ],
      },
      {
        name: 'RunRule2',
        id: $.formulaPackage.name + self.name,
        description: '<p>Western Electric Run Rule Two. \nThis function creates a condition when two out of three consecutive points fall beyond the 2σ limit (in Zone A or beyond), on the same side of the centerline.</p>',
        formula: "    //Create step-interpolated signal to keep from capturing the linear interpolation between sample points\n    $signalStep = $signal.toStep($maxinterp)\n\n    //create capsules for every 3 samples ($toCapsulesbyCount) and for every sample ($toCapsules)\n    $toCapsulesbyCount = $signalStep.toCapsulesByCount(3, 3*$maxinterp) //set the maximum duration based on the longest time you would expect to collect 3 samples\n    $toCapsules = $signalStep.toCapsules()\n\n    //Create condition for when the signal is not between +/-2 sigma limits\n    //separate upper and lower to capture when the rule violations occur on the same side of the centerline\n    $condLess = ($signalStep <= $minus2sd).shrink(1ns)\n    $condGreater = ($signalStep >= $plus2sd).shrink(1ns)\n\n    //within 3 data points ($toCapsulesByCount), count how many sample points ($toCapsules) are not between +/-2 sigma limits\n    $countLess = $toCapsules.touches($condLess).aggregate(count(),$toCapsulesbyCount,durationKey())\n    $countGreater = $toCapsules.touches($condGreater).aggregate(count(),$toCapsulesbyCount,durationKey())\n\n    //Find when 2+ out of 3 are outside of +/-2 sigma limits \n    //by setting the count as a property on $toCapsulesByCount and keeping only capsules greater than or equal to 2\n    $RR2below = $toCapsulesbyCount.setProperty('Run Rule 2 Violations', $countLess, endvalue())\n    .keep('Run Rule 2 Violations', isGreaterThanOrEqualto(2))\n    $RR2above = $toCapsulesbyCount.setProperty('Run Rule 2 Violations', $countGreater, endvalue())\n    .keep('Run Rule 2 Violations', isGreaterThanOrEqualto(2))\n\n    //Find every sample point capsule that touches a run rule violation capsule\n    //Combine upper and lower into one condition and use merge to combine overlapping capsules and to remove properties\n    $toCapsules.touches($RR2below or $RR2above).merge(true)\n  ",
        type: 'UserDefinedFormulaFunction',
        parameters: [
          {
            unbound: true,
            name: 'signal',
            formula: '1.toSignal()',
          },
          {
            unbound: true,
            name: 'minus2sd',
            formula: '1.toSignal()',
          },
          {
            unbound: true,
            name: 'plus2sd',
            formula: '1.toSignal()',
          },
          {
            unbound: true,
            name: 'maxinterp',
            formula: '1d',
          },
        ],
      },
      {
        name: 'RunRule3',
        id: $.formulaPackage.name + self.name,
        description: '<p>Western Electric Run Rule Three. This function creates a condition when four out of five consecutive points fall beyond the 1σ-limit (in Zone A or beyond), on the same side of the centerline.</p>',
        formula: "// Create a step-interpolated signal to keep from capturing the linear interpolation between sample points\n$signalStep = $signal.toStep($maxinterp)\n\n// Create capsules for every 5 samples ($toCapsulesbyCount) and for every sample ($toCapsules)\n$toCapsulesbyCount = $signalStep.toCapsulesByCount(5, 5*$maxinterp) // Set the maximum duration based on the longest time you would expect to collect 5 samples\n$toCapsules = $signalStep.toCapsules()\n\n// Create condition for when the signal is not between +/-1 sigma limits\n$condLess = ($signalStep <= $minus1sd).shrink(1ns)\n$condGreater = ($signalStep >= $plus1sd).shrink(1ns)\n\n// Within 5 data points ($toCapsulesByCount), count how many sample points ($toCapsules) are not between +/-1 sigma limits\n$countLess = $toCapsules.touches($condLess).aggregate(count(),$toCapsulesbyCount,durationKey())\n$countGreater = $toCapsules.touches($condGreater).aggregate(count(),$toCapsulesbyCount,durationKey())\n\n// Find when 4+ out of 5 are outside of +/-1 sigma limits \n// by setting the count as a property on $toCapsulesByCount and keeping only capsules greater than or equal to 4\n$RR3below = $toCapsulesbyCount.setProperty('Run Rule 3 Violations', $countLess, endvalue())\n.keep('Run Rule 3 Violations', isGreaterThanOrEqualto(4))\n$RR3above = $toCapsulesbyCount.setProperty('Run Rule 3 Violations', $countGreater, endvalue())\n.keep('Run Rule 3 Violations', isGreaterThanOrEqualto(4))\n\n// Find every sample point capsule that touches a run rule violation capsule\n// Combine upper and lower into one condition and use merge to combine overlapping capsules and to remove properties\n$toCapsules.touches($RR3below or $RR3above).merge(true)",
        type: 'UserDefinedFormulaFunction',
        parameters: [
          {
            unbound: true,
            name: 'signal',
            formula: '1.toSignal()',
          },
          {
            unbound: true,
            name: 'minus1sd',
            formula: '1.toSignal()',
          },
          {
            unbound: true,
            name: 'plus1sd',
            formula: '1.toSignal()',
          },
          {
            unbound: true,
            name: 'maxinterp',
            formula: '1d',
          },
        ],
      },
      {
        name: 'RunRule4',
        id: $.formulaPackage.name + self.name,
        description: '<p>Western Electric Run Rule Four. This function creates a condition when a trend exists in a time-ordered dataset. A trend is defined as 6 or more consecutive points continuously increasing or decreasing, not interrupted by a single data point in the opposite direction.</p>',
        formula: '//Create step-interpolated signal to keep from capturing the linear interpolation between sample points\n$signalStep = $signal.toStep()\n\n//create capsules for every 9 samples ($toCapsulesbyCount) and for every sample ($toCapsules)\n$toCapsulesbyCount = $signalStep.toCapsulesByCount(9,9*$maxinterp) //set the maximum duration based on the longest time you would expect to collect 5 samples\n$toCapsules = $signalStep.toCapsules()\n\n//Create condition for when the signal is either greater than or less than the mean\n//separate upper and lower to capture when the rule violations occur on the same side of the centerline\n$condLess = $signalStep.isLessThan($mean)\n$condGreater = $signalStep.isGreaterThan($mean) \n\n//Find when the last 9 samples are fully within the greater than or less than the mean\n//use merge to combine overlapping capsules and remove properties\n$toCapsules.touches(combinewith($toCapsulesbyCount.inside($condLess), $toCapsulesbyCount.inside($condGreater))).merge(true)',
        type: 'UserDefinedFormulaFunction',
        parameters: [
          {
            unbound: true,
            name: 'signal',
            formula: '1.toSignal()',
          },
          {
            unbound: true,
            name: 'mean',
            formula: '1.toSignal()',
          },
          {
            unbound: true,
            name: 'maxinterp',
            formula: '1d',
          },
        ],
      },
    ],
    docs: [
      {
        name: 'index',
        description: 'Allows creation of the four Western Electric Run Rules. Created based on Western Electric Run Rules.',
        title: 'Western Electric Run Rules',
        examples: {
          examples: [
            {
              description: 'Find when a sample point in a signal is above or below the control limits of +/-3 standard deviations from the mean.',
              formula: '$signal.WesternElectric_RunRule1($minus3sd, $plus3sd)',
            },
            {
              description: 'Find when a signal has 2 out 3 points above or below the +/-2 standard deviation limits.',
              formula: '$signal.WesternElectric_RunRule2($minus2sd, $plus2sd, $maxinterp)',
            },
            {
              description: 'Find when a signal has 4 out of 5 points above or below the +/-1 standard deviation limits.',
              formula: '$signal.WesternElectric_RunRule3($minus1sd, $plus1sd, $maxinterp)',
            },
            {
              description: 'Find when a signal has 9 consecutive points on the same side of the mean.',
              formula: '$signal.WesternElectric_RunRule4($mean, $maxinterp)',
            },
          ],
        },
      },
    ],
  }
