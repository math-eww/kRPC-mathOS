# kRPC-mathOS
## Kerbal Space Program kRPC programs

_A collection of classes and scripts for kRPC in Kerbal Space Program in Python_

**Requirements:**
Python 3
krpc (pip install krpc)

**Classes:**

_ManeuverAutopilot_: Simple autopilot to execute and plan nodes

_MathXORCoPilot_: Autopilot to handle launch, landing, hover and other functions

_InGameScreen_: Creates a 'screen' in game to display custom text information that can be sized/positioned and has support for two columns

_InGameConsole_: Using InGameScreen, creates a 'console' view to view output.  Stores a number of lines, and pushes lines out of the top when a new line is added to the bottom

**Modules:**

_consoleprint_: Print overrider, hijacks the print function to duplicate output to a InGameConsole.  Initialize in one file by calling setUpConsole, then import the print function in any file you want to print output to the InGameConsole

_mathos_: Main file to set up and run others
