@echo off 

if "%1" == "h" goto label
mshta vbscript:createobject("wscript.shell").run("""%~dp0%~nx0"" h",0)(window.close)&&exit 

:label
python %~dp0/Tagit.py