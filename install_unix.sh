
MIP_INSTALL="micropython -m mip install"

${MIP_INSTALL} https://emlearn.github.io/emlearn-micropython/builds/master/x64_6.3/emlearn_trees.mpy
${MIP_INSTALL} github:jonnor/micropython-npyfile
${MIP_INSTALL} https://raw.githubusercontent.com/emlearn/emlearn-micropython/refs/heads/master/examples/har_trees/timebased.py
${MIP_INSTALL} https://raw.githubusercontent.com/emlearn/emlearn-micropython/refs/heads/master/examples/har_trees/recorder.py
