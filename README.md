# CS 3700 Simple Bridge Project Starter Code

This repository contains the starter code for the CS 3700 Simple Bridge project, along with support code to test your project.  The files included are described below:

## Starter Code

The Python-based starter code located in the file `3700bridge.python`.  If you wish to use that code as a basis of your project, you should copy that file to a file named `3700bridge` (we recommend keeping the original around in case you need to refer back to it).  Recall that you can complete the project in other langauges if you wish, though you will need to write the code to connect to the UDP sockets yourself (importantly, recall that you need to create a *separate* UDP socket per LAN, otherwise you will not receive all messages).

## Configurations

The configurations we provide are located in the `configs/` folder, with one file per configuration.  You are free to create additional configurations if you wish, but we recommend not modifying the provided configurations.

## Simulator

The simulator is located in the file `run`, and you run it by simply providing the path to the configuration you wish to run.  For example, you can run `./run configs/simple-1.conf`, which will run that particular configuration.  Details on the output are provided in the project description.

## Testing Code

Finally, we provide a script that tests *all* default configurations, and determines whether your code passes them.  You can run it by simly running `./test`.  Details on the output are provided in the project description.

## Updates

We may periodically push out bug fixes to the `run` and `test` scripts.  If you need to get these updates, simply run

git pull

and it will bring down new versions,