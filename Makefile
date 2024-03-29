######################################################################
##        Copyright (c) 2022 Carsten Wulff Software, Norway
## ###################################################################
## Created       : wulff at 2022-5-28
## ###################################################################
##  The MIT License (MIT)
##
##  Permission is hereby granted, free of charge, to any person obtaining a copy
##  of this software and associated documentation files (the "Software"), to deal
##  in the Software without restriction, including without limitation the rights
##  to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
##  copies of the Software, and to permit persons to whom the Software is
##  furnished to do so, subject to the following conditions:
##
##  The above copyright notice and this permission notice shall be included in all
##  copies or substantial portions of the Software.
##
##  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
##  IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
##  FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
##  AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
##  LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
##  OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
##  SOFTWARE.
##
######################################################################

#-  Copy from https://gist.github.com/sighingnow/deee806603ec9274fd47
OSFLAG 				:=
ifeq ($(OS),Windows_NT)
	OSFLAG = win
else
	UNAME_S := $(shell uname -s)
	ifeq ($(UNAME_S),Linux)
	OSFLAG = linux
	endif
	ifeq ($(UNAME_S),Darwin)
	OSFLAG = osx
	endif

endif

sid_refl = 685097948
#sid_init = 685751234
sid_init = 685701409

current_dir = $(shell pwd)

nrfjprog = nrfjprog.exe

ifeq ($(OSFLAG),win)
	pycmd = /usr/bin/python3
	#sid_refl = 685649956
	#sid_init = 685965072
	sid_init = 685369056
	sid_refl = 685868684


else
ifeq ($(OSFLAG),linux)


	nrfjprog = nrfjprog.exe
	pycmd = python3
else
	nrfjprog = nrfjprog
endif
endif

first:
	cd reflector; west build -b nrf52833dk_nrf52833 -- -DCONF_FILE=prj.conf
	cd initiator; west build -b nrf52833dk_nrf52833 -- -DCONF_FILE=prj.conf

flashr:
	cd reflector; west flash -i ${sid_refl}
	${MAKE} -f Makefile reset SID=${sid_refl}

flashi:
	cd initiator; west flash -i ${sid_init}
	${MAKE} -f Makefile reset SID=${sid_init}


reset:
	${nrfjprog} -p -s ${SID} && ${nrfjprog} -r -s ${SID}


doc:
	pandoc --from gfm README.md -o README.html

clean:
	rm -rf initiator/build
	rm -rf reflector/build
