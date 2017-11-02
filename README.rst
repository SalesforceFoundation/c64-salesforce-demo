c64-salesforce-client and c64-serial-proxy
==========================

For the Dreamforce 2017 session `New Life for a Commodore 64: An Old-Is-New-Again Salesforce Client`.

https://success.salesforce.com/Sessions#/session/a2q3A000001ytadQAA


See the README in c64-serial-proxy for instructions about the python proxy.


Do make this work as-is, you'll want to install the VICE emulator, and the ACME 6502 assembler.


Build Demo 1 BASIC Client
-------------------------

```
petcat -w2 -o sfdc.prg -- sfdc.bas
```

```
c1541 -format sfdc,id d64 sfdc.d64 -write sfdc.prg sfdc
```


Build Demo 2 Assembly Client
----------------------------

```
acme --cpu 6510 --format cbm --outfile blink.prg macros.asm irpt.asm rs232.asm defs.asm
```

```
c1541 -format blink,id d64 blink.d64 -write blink.prg blink
```
