include $(dir $(MAKEFILE_LIST))../common.mk

all:
	mkdir build
	cd build ; $(CXX) $(CXXFLAGS) ../src/main.cpp -o testcase

run: json

json:
	cd build ; ./testcase
	chmod $(if $(filter Darwin,$(HOST_OS) $(OSTYPE)),0455,0555) src build
	$(GCOVR) --verbose --json-pretty --json coverage.json --gcov-ignore-errors=output_error --root src build

clean:
	chmod 0755 src build 2>/dev/null ; exit 0
	rm -rf build
	rm -f *.gc*
	rm -f coverage.json
