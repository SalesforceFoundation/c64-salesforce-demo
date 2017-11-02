c64-serial-proxy
==========================

For the Dreamforce 2017 session `New Life for a Commodore 64: An Old-Is-New-Again Salesforce Client`.

https://success.salesforce.com/Sessions#/session/a2q3A000001ytadQAA


For the proxy to authenticate to your Salesforce org, populate these environment variables in your shell:

SALESFORCE_USERNAME
SALESFORCE_PASSWORD (optional; if you leave this unset, you will be prompted to enter it when you start the proxy)
SALESFORCE_CLIENT_ID
SALESFORCE_CLIENT_SECRET


Running the python serial proxy
-------------------------------

Before your first try, use virtualenv and pip (or whatever approach you prefer) to install dependencies.  The simplest way is

```
python setup.py install
```

This might require su access.


To run the proxy, first use the `socat` utility to set up a serial connection between your host and the VICE C64 emulator:

```
socat -d -d pty,raw,echo=0,ispeed=2400,ospeed=2400 pty,raw,echo=0,ispeed=2400,ospeed=2400
```

Note what socat outputs as the two endpoint devices for the serial connection.  Pick one, and configure VICE to use it as the RS232 connection.  The other endpoint device name will be used as an argument when you start the proxy.  For the purpose of the commands below, we'll call this device `/dev/ttys010`.


In another terminal, run the following command for Demo 1:

```
c64-serial-proxy /dev/ttys010
```

For Demo 2:

```
c64-serial-proxy -s /dev/ttys010
```

To quit the proxy, enter `control-quit` in the terminal where the proxy is running and hit enter.  Or just control-c.
