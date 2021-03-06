"""
Idiot check for sshd / Remote Login

purpose: indicates if "Sharing Preferences: Remote Login" is enabled or
    OpenSSH's sshd is otherwise running

daemon:
    /usr/sbin/sshd

requirement: sshd provides interactive access with valid creds. Best left off.
This checks both launchd enabling sshd and manually starting sshd.

info:
Detecting this is tricky because until it's accessed launchd hasn't
forked the sshd process so there's nothing visible in process table.
While a system is being accessed (or scanned even), though, the sshd process
is visible. Once a session ends (or login times out) the sshd process exits
leaving launchd to listen for the SSH client to connect

The correct way to check for this being enabled is using launchctl
checking output of:

$ launchctl print system/com.openssh.sshd state

which would have state = waiting which indicates it's configured to spawn sshd.
If it's not enabled in Sharing prefs nothing will be returned:

    $ launchctl print system/com.openssh.sshd state
    Could not find service "com.openssh.sshd" in domain for system

checking the pid is easier and, much more importantly, would catch
a manually invoked sshd left behind from, say, an rsync serving or a breach
(you pick)

"""
import logging
import subprocess
import os
import psutil

import idiot
from idiot import CheckPlugin

log = logging.getLogger()

class SSHDCheck(CheckPlugin):
    name = "sshd"

    def run(self):
        with open(os.devnull, 'w') as devnull:
            try:
                # If the service is disabled in Preferences
                # the query returns a non-zero error
                # should use this query better in future
                if subprocess.check_call(['launchctl', 'print', 'system/com.openssh.sshd'], stdout=devnull, stderr=devnull):
                    return (True, "disabled")
                else:
                    return (False, "enabled in Sharing Prefs: Remote Login")
            except subprocess.CalledProcessError as e:
                # this only gets run if sshd isn't enabled by
                # launchd as checked above
                pids = []
                for p in psutil.process_iter():
                    try:
                        if p.name() == 'sshd':
                            pids.append(p.pid)
                    except psutil.NoSuchProcess:
                        pass
                if len(pids):
                    return (False, "enabled manually - see pids: {} ".format(', '.join([str(p) for p in pids])))
                else:
                    return (True, "disabled")

if __name__ == "__main__":
    print(SSHDCheck().run())
