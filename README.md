# kRPC-mathOS
## Kerbal Space Program kRPC programs

### A collection of classes and scripts for kRPC in Kerbal Space Program in Python

**Requirements:**

_Python 3_

_krpc (pip install krpc)_

**Classes:**

_ManeuverAutopilot_: Simple autopilot to execute and plan nodes

_MathXORCoPilot_: Autopilot to handle launch, landing, hover and other functions

_InGameScreen_: Creates a 'screen' in game to display custom text information that can be sized/positioned and has support for two columns

_InGameConsole_: Using InGameScreen, creates a 'console' view to view output.  Stores a number of lines, and pushes lines out of the top when a new line is added to the bottom

**Modules:**

_consoleprint_: Print overrider, hijacks the print function to duplicate output to a InGameConsole.  Initialize in one file by calling setUpConsole, then import the print function in any file you want to print output to the InGameConsole

_mathos_: Main file to set up and run others

## Project Status

Haven't been playing KSP for a little while now, I'm sure I'll be back though.
### How Can I Help?
Make some changes and throw up a pull request!

## License

The software is licensed under the GPL license. See the LICENSE file for full copyright and license text. Any modifications to or software including GPL-licensed code must also be made available under the GPL.
