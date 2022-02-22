@echo off
REM (start, step, stop)
for /l %%x in (15, 1, 25) do python ourTW.py -c 0 111 -r 0 223 -i 1 40 -t %%x
