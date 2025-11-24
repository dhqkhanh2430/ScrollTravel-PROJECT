#It is important that all members of the group must read and do exactly as this file says!!
(USE PYTHON 3.11)

---|SETTING UP|---
(IGNORE THIS IF YOU HAVE ALREADY DONE IT ONCE)
#FIRST STEP: Clone the repo into your local machine (use cmd or clone it manually in gitdesktop).

#SECOND STEP: Open cmd and navigate to the project you just cloned (in cmd type "cd [your-project-folder]").

#THIRD STEP: Create a virtual environment (cmd -> python -m venv venv) and activate it (cmd -> ".\venv\Scripts\activate").

#FOURTH STEP: When you virtual environment is successfully activated, do "pip install -r requirements.txt" in cmd to install all the required libraries.

---|GUIDANCE|---
#It is important to convert .qrc file into a .py file (since python dont understand XML files), how to do this: 
    +Make sure that your virtual environment is activated.
    +Navigate your terminal into the folder where you located the file (use "cd (the path to the folder contains the file)).
    +Type: "pyrcc5 res.qrc -o res_rc.py".
    +After you are done doing that, copy all the .qrc and .py with all the assets into ASSETS folders in git (do it respectively).
#To open QT Designer, navigate to "[where-you-stored-your-repo]\GitHub\ScrollTravel-PROJECT\venv\Lib\site-packages\qt5_applications\Qt\bin" and look for "designer.exe".
#For further more guidance, check these documents out: 
https://www.pythonguis.com/tutorials/qt-designer-gui-layout/
https://doc.qt.io/qt-6/qtdesigner-manual.html

---|NOTE|---
#It is required to activate your virtual environment first everytime you start working on the project.
#If you have any questions or in need for help please text other members in the group chat!

