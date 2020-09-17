import os
os.chdir("../")

import sys
sys.path.append(".")

import main
import waitress

waitress.serve(main.app, host='127.0.0.1', port=8080, threads=1) #WAITRESS!