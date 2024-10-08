function(suffix='')
  {
    formulaPackage: {
      name: 'NelsonRunRules' + suffix,
      creatorName: 'Christopher Harp',
      creatorContactInfo: 'christopher.harp@seeq.com',
    },
    functions: [
      {
        name: 'RunRule1',
        id: $.formulaPackage.name + self.name,
        description: '<p>Nelson Run Rule One. This function creates a condition when any single data point falls outside the control limits from the centerline (i.e., any point that falls outside Zone A, beyond either the upper or lower control limit).</p>',
        formula: '$signalStep = $signal.toStep() \n ($signalStep < $minus3sd or $signalStep > $plus3sd)',
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
        description: '<p>This function creates a condition when 9 consecutive points fall on the same side of the centerline (in Zone C or beyond).</p>',
        formula: '//Create step-interpolated signal to keep from capturing the linear interpolation between sample points \n $signalStep = $signal.toStep() \n //create capsules for every 9 samples ($toCapsulesbyCount) and for every sample ($toCapsules) \n $toCapsulesbyCount = $signalStep.toCapsulesByCount(9,9*$maxinterp) //set the maximum duration based on the longest time you would expect to collect 5 samples \n $toCapsules = $signalStep.toCapsules() \n //Create condition for when the signal is either greater than or less than the mean \n//separate upper and lower to capture when the rule violations occur on the same side of the centerline \n $condLess = $signalStep.isLessThan($mean) \n $condGreater = $signalStep.isGreaterThan($mean)  \n //Find when the last 9 samples are fuly within the greater than or less than the mean \n //use merge to combine overlapping capsules and remove properties \n $toCapsules.touches(combinewith($toCapsulesbyCount.inside($condLess), $toCapsulesbyCount.inside($condGreater))).merge(true)',
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
      {
        name: 'RunRule3',
        id: $.formulaPackage.name + self.name,
        description: '<p>Nelson Run Rule Three.\nThis function creates a condition when any six consecutive data points are increasing or decreasing.</p>',
        formula: "//Create step-interpolated signal to keep from capturing the linear interpolation between sample points\n$signalStep = $signal.toStep()\n\n//create capsules for every 6 samples ($toCapsulesbyCount) and for every sample ($toCapsules)\n$toCapsulesbyCount = $signalStep.toCapsulesByCount(6,6*$maxinterp) //set the maximum duration based on the longest time you would expect to collect 5 samples\n$toCapsules = $signalStep.toCapsules()\n\n//Create condition for when the signal is increasing or decreasing\n//separate increasing and decreasing to capture when the rule violations occur in each direction\n$condIncreasing = ($signalStep.runningDelta() > 0)\n$condDecreasing = ($signalStep.runningdelta() < 0)\n\n//within 6 data points ($toCapsulesByCount), count how many sample points ($toCapsules) are increasing or decreasing\n$countIncreasing = $signal.todiscrete().remove($condIncreasing.inverse()).aggregate(count(),$toCapsulesbyCount.move(1ns,0), durationkey())\n$countDecreasing = $signal.todiscrete().remove($condDecreasing.inverse()).aggregate(count(),$toCapsulesbyCount.move(1ns,0), durationkey())\n\n//Find when 6 out of 6 are increasing or decreasing\n//by setting the count as a property on $toCapsulesByCount and keeping only capsules greater than or equal to 6\n$RR3Increasing = $toCapsulesbyCount.setProperty('Run Rule 3 Violations', $countIncreasing, endvalue())\n.keep('Run Rule 3 Violations', isGreaterThanorEqualto(5))\n$RR3Decreasing = $toCapsulesbyCount.setProperty('Run Rule 3 Violations', $countDecreasing, endvalue())\n.keep('Run Rule 3 Violations', isGreaterThanorEqualto(5))\n\n//Find every sample point capsule ($toCapsules) that touches a run rule violation capsule\n//Combine increasing and decreasing into one condition and use merge to combine overlapping capsules and to remove properties\n$toCapsules.touches($RR3Increasing or $RR3Decreasing).merge(true)",
        type: 'UserDefinedFormulaFunction',
        parameters: [
          {
            unbound: true,
            name: 'signal',
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
        description: '<p>Nelson Run Rule Four. \nThis function creates a condition when fourteen consecutive data points are alternating in direction (i.e. increasing then decreasing).</p>',
        formula: "//Create step-interpolated signal to keep from capturing the linear interpolation between sample points\n$signalStep = $signal.toStep()\n\n//create capsules for every 14 samples ($toCapsulesbyCount), every 2 samples ($EveryTwoSamples), and for every sample ($toCapsules)\n$toCapsulesbyCount = $signalStep.toCapsulesByCount(14, 14*$maxinterp) //set the maximum duration based on the longest time you would expect to collect 14 samples\n$EveryTwoSamples = $signalStep.toCapsulesByCount(2, 2*$maxinterp)\n$toCapsules = $signalStep.toCapsules()\n\n//Create condition for when the signal is increasing or decreasing\n//separate increasing and decreasing to capture when the rule violations occur in each direction\n$delta = $signalStep.runningdelta(startkey())\n$condIncreasing = ($delta >= 0)\n$condDecreasing = ($delta <= 0)\n\n//Create a condition for times when every other sample does not alternate between increasing and decreasing\n$condNotAlternating = combinewith($EveryTwoSamples.inside($condDecreasing.move(1ns).merge(true)), $EveryTwoSamples.inside($condIncreasing.move(1ns).merge(true)))\n\n//Remove the data points when the trend of the data on both sides of that data point is not alternating direction\n$countNotAlternating = $signal.todiscrete().remove($condNotAlternating.afterstart(1ns)).aggregate(count(),$toCapsulesbyCount.shrink(1ns), durationkey()).move(1ns)\n\n//Find when the 12 internal samples (excluding the first and last data point in the last 14 samples) are all alternating directions\n//Use merge to combine overlapping capsules and to remove properties\n$toCapsules.touches($toCapsulesbyCount.setProperty('Run Rule 4 Violations', $countNotAlternating, endvalue())\n.keep('Run Rule 4 Violations', isGreaterThanorEqualto(12))).merge(true)",
        type: 'UserDefinedFormulaFunction',
        parameters: [
          {
            unbound: true,
            name: 'signal',
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
        name: 'RunRule5',
        id: $.formulaPackage.name + self.name,
        description: '<p>Nelson Run Rule Five. \n This function creates a condition when two out of three consecutive points fall beyond the 2σ limit (in Zone A or beyond), on the same side of the centerline.</p>',
        formula: "//Create step-interpolated signal to keep from capturing the linear interpolation between sample points\n$signalStep = $signal.toStep()\n\n//create capsules for every 3 samples ($toCapsulesbyCount) and for every sample ($toCapsules)\n$toCapsulesbyCount = $signalStep.toCapsulesByCount(3,3*$maxinterp) //set the maximum duration based on the longest time you would expect to collect 3 samples\n$toCapsules = $signalStep.toCapsules()\n\n//Create condition for when the signal is not between +/-2 sigma limits\n//separate upper and lower to capture when the rule violations occur on the same side of the centerline\n$condLess = ($signalStep <= $minus2sd)\n$condGreater = ($signalStep >= $plus2sd)\n\n//within 3 data points ($toCapsulesByCount), count how many sample points are not between +/-2 sigma limits\n$countLess = $signal.todiscrete().remove(not $condLess).aggregate(count(),$toCapsulesbyCount,durationKey())\n$countGreater = $signal.todiscrete().remove(not $condGreater).aggregate(count(),$toCapsulesbyCount,durationKey())\n\n//Find when 2+ out of 3 are outside of +/-2 sigma limits \n//by setting the count as a property on $toCapsulesByCount and keeping only capsules greater than or equal to 2\n$RR5below = $toCapsulesbyCount.setProperty('Run Rule 5 Violations', $countLess, endvalue())\n.keep('Run Rule 5 Violations', isGreaterThanOrEqualto(2))\n$RR5above = $toCapsulesbyCount.setProperty('Run Rule 5 Violations', $countGreater, endvalue())\n.keep('Run Rule 5 Violations', isGreaterThanOrEqualto(2))\n\n//Find every sample point capsule that touches a run rule violation capsule\n//Combine upper and lower into one condition and use merge to combine overlapping capsules and to remove properties\n$toCapsules.touches($RR5below or $RR5above).merge(true)",
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
        name: 'RunRule6',
        id: $.formulaPackage.name + self.name,
        description: '<p>This function creates a condition when four out of five consecutive points fall beyond the 1σ limit (in Zone B or beyond), on the same side of the centerline.</p>',
        formula: "//Create step-interpolated signal to keep from capturing the linear interpolation between sample points\n$signalStep = $signal.toStep()\n\n//create capsules for every 5 samples ($toCapsulesbyCount) and for every sample ($toCapsules)\n$toCapsulesbyCount = $signalStep.toCapsulesByCount(5,5*$maxinterp) //set the maximum duration based on the longest time you would expect to collect 5 samples\n$toCapsules = $signalStep.toCapsules()\n\n//Create condition for when the signal is not between +/-1 sigma limits\n//separate upper and lower to capture when the rule violations occur on the same side of the centerline\n$condLess = ($signalStep <= $minus1sd)\n$condGreater = ($signalStep >= $plus1sd)\n\n//within 5 data points ($toCapsulesByCount), count how many sample points ($toCapsules) are not between +/-1 sigma limits\n$countLess = $signal.toDiscrete().remove(not $condLess).aggregate(count(),$toCapsulesbyCount, durationkey())\n$countGreater = $signal.toDiscrete().remove(not $condGreater).aggregate(count(),$toCapsulesbyCount,durationkey())\n\n//Find when 4+ out of 5 are outside of +/-1 sigma limits\n//by setting the count as a property on $toCapsulesByCount and keeping only capsules greater than or equal to 4\n$RR6below = $toCapsulesbyCount.setProperty('Run Rule 6 Violations', $countLess, endvalue())\n.keep('Run Rule 6 Violations', isGreaterThanOrEqualto(4))\n$RR6above = $toCapsulesbyCount.setProperty('Run Rule 6 Violations', $countGreater, endvalue())\n.keep('Run Rule 6 Violations', isGreaterThanOrEqualto(4))\n\n//Find every sample point capsule ($toCapsules) that touches a run rule violation capsule\n//Combine upper and lower into one condition and use merge to combine overlapping capsules and to remove properties\n$toCapsules.touches($RR6below or $RR6above).merge(true)",
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
        name: 'RunRule7',
        id: $.formulaPackage.name + self.name,
        description: '<p>Nelson Run Rule Seven. This function creates a condition when fifteen consecutive points fall within the 1σ limit from the mean (in Zone C).</p>',
        formula: "//Create step-interpolated signal to keep from capturing the linear interpolation between sample points\n$signalStep = $signal.toStep()\n\n//create capsules for every 15 samples ($toCapsulesbyCount) and for every sample ($toCapsules)\n$toCapsulesbyCount = $signalStep.toCapsulesByCount(15,15*$maxinterp) //set the maximum duration based on the longest time you would expect to collect 15 samples\n$toCapsules = $signalStep.toCapsules()\n\n//Create condition for when the signal is between +/-1 sigma limits\n$condWithin = ($signalStep >= $minus1sd and $signalStep <= $plus1sd)\n\n//within 15 data points ($toCapsulesByCount), count how many sample points ($toCapsules) are between +/-1 sigma limits\n$countWithin = $signal.toDiscrete().remove(not $condWithin).aggregate(count(),$toCapsulesbyCount, durationkey())\n\n//Find when 15 out of 15 are within +/-1 sigma limits\n//by setting the count as a property on $toCapsulesByCount and keeping only capsules equal to 15\n$RR7 = $toCapsulesbyCount.setProperty('Run Rule 7 Violations', $countWithin, endvalue())\n.keep('Run Rule 7 Violations', isEqualto(15))\n\n//Find every sample point capsule ($toCapsules) that touches a run rule violation capsule\n//Use merge to combine overlapping capsules and to remove properties\n$toCapsules.touches($RR7).merge(true)",
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
        name: 'RunRule8',
        id: $.formulaPackage.name + self.name,
        description: '<p>Nelson Run Rule Eight. This function creates a condition when eight consecutive points fall beyond the 1σ limit (in Zone B or beyond), with points in both directions from the mean.</p>',
        formula: "//Create step-interpolated signal to keep from capturing the linear interpolation between sample points\n$signalStep = $signal.toStep()\n\n//create capsules for every 8 samples ($toCapsulesbyCount) and for every sample ($toCapsules)\n$toCapsulesbyCount = $signalStep.toCapsulesByCount(8,8*$maxinterp) //set the maximum duration based on the longest time you would expect to collect 8 samples\n$toCapsules = $signalStep.toCapsules()\n\n//Create condition for when the signal is not between +/-1 sigma limits\n//separate upper and lower and combined to capture when the rule violations occur on the same side of the centerline\n$condLess = ($signalStep <= $minus1sd)\n$condGreater = ($signalStep >= $plus1sd)\n$condEither = (($signalStep <= $minus1sd) or ($signalStep >= $plus1sd))\n\n//within 8 data points ($toCapsulesByCount), count how many sample points are not between +/-1 sigma limits\n$countEither = $signal.toDiscrete().remove(not $condEither).aggregate(count(),$toCapsulesbyCount,durationkey())\n\n//Find when 8 consecutive points are outside of +/-1 sigma limits, with points on each side of the mean\n//by setting the count as a property on $toCapsulesByCount and keeping only capsules greater than or equal to 4\n$RR8 = $toCapsulesbyCount.setProperty('Run Rule 8 Violations', $countEither, endvalue())\n.keep('Run Rule 8 Violations', isGreaterThanOrEqualto(8)).touches($condLess).touches($condGreater)\n\n//Find every sample point capsule ($toCapsules) that touches a run rule violation capsule\n//Combine upper and lower into one condition, use merge to combine overlapping capsules and remove properties, and set property for run rule\n$toCapsules.touches($RR8).merge(true)",
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
    ],
    docs: [
      {
        name: 'index',
        description: 'Allows creation of the Nelson Run Rules. Created based on Nelson Run Rules.',
        title: 'Nelson Run Rules',
        examples: {
          examples: [
            {
              description: 'Find when a sample point in a signal is above or below the control limits of +/-3 standard deviations from the mean.',
              formula: '$signal.Nelson_RunRule1($minus3sd, $plus3sd)',
            },
            {
              description: 'Find when a signal has 9 consecutive points on the same side of the mean.',
              formula: '$signal.Nelson_RunRule2($mean, $maxinterp)',
            },
            {
              description: 'Find when 6 consecutive data points are increasing or decreasing in trend.',
              formula: '$signal.Nelson_RunRule3($maxinterp)',
            },
            {
              description: 'Find when 14 consecutive data points are alternating in direction (increasing followed by decreasing).',
              formula: '$signal.NelsonRunRule4($maxinterp)',
            },
            {
              description: 'Find when a signal has 2 out 3 points above or below the +/-2 standard deviation limits.',
              formula: '$signal.NelsonRunRule5($minus2sd, $plus2sd, $maxinterp)',
            },
            {
              description: 'Find when a signal has 4 out of 5 points above or below the +/-1 standard deviation limits.',
              formula: '$signal.NelsonRunRule6($minus1sd, $plus1sd, $maxinterp)',
            },
            {
              description: 'Find when a signal has 15 consecutive points within the +/-1 standard deviation limits.',
              formula: '$signal.NelsonRunRule7($minus1sd, $plus1sd, $maxinterp)',
            },
            {
              description: 'Find when a signal has 8 consecutive points beyond the +/-1 standard deviation limits, with points in both directions from the mean.',
              formula: '$signal.Nelson_RunRule8($minus1sd, $plus1sd, $maxinterp)',
            },
          ],
        },
      },
    ],
  }
