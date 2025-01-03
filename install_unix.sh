
MIP_INSTALL="micropython -m mip install"

${MIP_INSTALL} https://emlearn.github.io/emlearn-micropython/builds/master/x64_6.3/emlearn_trees.mpy
${MIP_INSTALL} github:jonnor/micropython-npyfile
${MIP_INSTALL} https://github.com/emlearn/emlearn-micropython/raw/refs/heads/master/examples/har_trees/recorder.py
${MIP_INSTALL} https://github.com/emlearn/emlearn-micropython/raw/refs/heads/master/examples/har_trees/timebased.py
