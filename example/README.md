# Examples
This directory contains some example scripts that are using fparser.

## fparser2_f2008.py
This is a simple Python script to show that fparser can handle separate
modules and subroutines in one file. It parses a simple Fortran
code specified as a string in the Python script, and then prints the
parsed code to stdout.

## create_dependencies.py
This program prints dependencies between Fortran source files to stdout,
in a format suitable to be used in a Makefile. Usage:

	  $ $(PATH_TO_FPARSER)/example/create_dependencies.py *f90
	  configuration_mod.o: base_mesh_config_mod.o extrusion_uniform_config_mod.o \
		  finite_element_config_mod.o io_utility_mod.o partitioning_config_mod.o \
		  perturbation_bell_config_mod.o planet_config_mod.o timestepping_config_mod.o
	  write_diagnostics_mod.o: write_methods_mod.o

It also supports files in subdirectories, e.g.:

    fparser/example$ ./create_dependencies.py  test_files/*f90
    test_files/b.o: test_files/a.o
    test_files/c.o: test_files/a.o test_files/b.o

### Known issues:
- If you do not have ``python`` in your path (e.g. you have only ``python3``
  installed), you have to either invoke the script using:

      python3 $(PATH_TO_FPARSER)/example/create_dependencies.py *.f90
  or modify the first line of the script to use ``python3`` instead of
  ``python``.
- The script will only detect dependencies from the files specified on the
  command line to files provided on the command line. It assumes that the name
  in the ``use`` statement is the same as the file name that stores the module.
  For example, if your code has:

  	  use mymodule

  then the script will look for a file with the 'root' name ``mymodule``,
  e.g. it would use ``mymodule.f90``, ``mymodule.F90``, or ``mymodule.x90``
  in the list of files provided as argument. If no matching file is found, no
  dependencies will be printed for this case, it will be silently ignored.
  You can modify the ``create_dependency.py`` script if you are using a
  different naming style for your files (see lines 120 to 123 in the script).

### Todo
- Remove the need for a file naming convention by parsing all files, and then
  using this information to find dependencies.
- Support dependencies to other libraries, e.g.:

      $ ./create_dependencies.py -l NETCDF_LIB=/opt/mynetcdf-dir my_netcdf_source.f90
      my_netcdf_source.o: $(NETCDF_LIB)
- Provide a list of modules to ignore, and abort the script if a reference
  to a module is found that is unknown (i.e. neither provided in a file name
  nor in the list of modules to ignore).

## split_file.py
This script splits one Fortran source file into several files, each containing
one top level module, subroutine, function or program. Each file uses the name
of the program unit (module-, subroutine-, function-, program name). The
extension will be ``.F90`` if there are preprocessor directives in the file,
and ``.f90`` otherwise.

Additionally, ``split_file.py`` will create a Makefile to build either the
binary (if a program is found in the file), or all object files. If any of
the environment variables ``F90``, ``F90FLAGS``, and ``LDFLAGS`` are set at
run time of the script, it will use these values as default values in the
makefile. But by setting these environment variables when running ``make``,
these defaults can always be overwritten. The Makefile also has a ``clean``
target, which will remove all ``.mod``, object, and the program file (if
available). It uses the ``create_dependencies.py`` script to add the
required dependencies to the Makefile.
