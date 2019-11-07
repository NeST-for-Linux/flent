# -*- coding: utf-8 -*-
#
# __init__.py
#
# Author:   Toke Høiland-Jørgensen (toke@toke.dk)
# Date:      6 December 2012
# Copyright (c) 2012-2016, Toke Høiland-Jørgensen
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from __future__ import absolute_import, division, print_function, unicode_literals

import locale
import os
import signal
import sys
from importlib import import_module
import subprocess
import threading
import time
# import user_script

def exec_subprocess(cmd, block=True):
    temp = subprocess.Popen(cmd.split())
    if block:
        temp.communicate()
    else:
        pass
    
def server(ns):
    # run netserver
    print('server: {}'.format(ns))
    exec_subprocess('ip netns exec ' + ns + ' netserver')
    print('ip netns exec ' + ns + ' netserver')

def client(ns, cmd, server_ip):
    print('client: {} {} {}'.format(ns, cmd, server_ip))
    # TODO: Run flent with appropriate arguements
    # exec_subprocess('ip netns exec {} traceroute 10.2.2.2'.format(ns))
    # exec_subprocess('ip netns exec n1 flent tcp_download -H 10.2.2.2 --length 1')
    # exec_subprocess('ip netns exec n1 flent tcp download -H 10.2.2.2 --length 1')
    exec_subprocess('ip netns exec ' + ns + ' ' + cmd + ' -H ' + server_ip + " --length 1")
    # + 'flent tcp_download -H 10.1.2.2 -p tcp_cwnd --socket-stats -o cwnd.png')
    print('ip netns exec ' + ns + ' ' + cmd + ' -H ' + server_ip + " --length 1")

# Convert SIGTERM into SIGINT to apply the same shutdown logic.
def handle_sigterm(sig, frame):
    os.kill(os.getpid(), signal.SIGINT)

def arg_parse():
    args = sys.argv[1:]
    # args_list = args.split()
    print(args)
    i = args.index("--topo")
    # args[i] = ''
    # args[i+1] = ''
    # print(args)
    args.remove(args[i])
    args.remove(args[i])
    print(args)

    new_args = 'flent'
    for arg in args:
        new_args += ' ' + arg
    print(new_args)
    return new_args
    
    

def run_flent(gui=False):
    if sys.version_info[:2] < (3, 5):
        sys.stderr.write("Sorry, Flent requires v3.5 or later of Python.\n")
        sys.exit(1)
    try:
        try:
            locale.setlocale(locale.LC_ALL, '')
        except locale.Error:
            pass
        from flent import batch
        from flent.settings import load
        from flent.loggers import setup_console, get_logger

        setup_console()
        logger = get_logger(__name__)

        try:
            signal.signal(signal.SIGTERM, handle_sigterm)
            settings = load(sys.argv[1:])
            if(settings.TOPO):
                sys.path.append(os.path.dirname(os.path.abspath(settings.TOPO)))
                print(os.path.dirname(os.path.abspath(settings.TOPO)))
                filename = os.path.basename(settings.TOPO)
                print(filename)
                topology = import_module(filename[:-3])
                (client_ns, client_ip, server_ns, server_ip) = topology.run()
                new_args = arg_parse()

                # exec_subprocess("ip netns exec n1 ping 10.2.2.2 -c 5")

                # TODO: Set server_ns and client_ns here

                t1 = threading.Thread(target=server, args=(server_ns, ))
                t2 = threading.Thread(target=client, args=(client_ns, new_args, server_ip, ))

                t1.start()
                time.sleep(2.0)
                t2.start()

                t1.join()
                t2.join()

                # run user script

                pass
            elif gui or settings.GUI:
                from flent.gui import run_gui
                return run_gui(settings)
            else:
                b = batch.new(settings)
                b.run()

        except RuntimeError as e:
            logger.exception(str(e))

    except KeyboardInterrupt:
        try:
            b.kill()
        except NameError:
            pass

        # Proper behaviour on SIGINT is re-killing self with SIGINT to properly
        # signal to surrounding shell what happened.
        # Ref: http://mywiki.wooledge.org/SignalTrap
        try:
            signal.signal(signal.SIGINT, signal.SIG_DFL)
            os.kill(os.getpid(), signal.SIGINT)
        except:
            return 1  # Just in case...
    finally:
        try:
            signal.signal(signal.SIGTERM, signal.SIG_DFL)
        except:
            pass
    return 0


def run_flent_gui():
    return run_flent(gui=True)


__all__ = ['run_flent', 'run_flent_gui']
