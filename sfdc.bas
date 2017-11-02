   10 open 2,2,0,chr$(10)+chr$(0)
   11 print "loading..."
   12 gosub 59050:rem make "cloud" icon
   13 dim rc$(50)
   14 gosub 16
   15 goto 20
   16 print chr$(147) + "c= client"
   17 return
   20 rem command loop
   21 ep$=""
   22 poke 198,3:poke 631,34:poke 632,34:poke 633,20
   23 input cm$
   24 poke 631,34:poke 632,34:poke 633,20
   25 goto 60000
   100 rem response loop
   111 ur$=""
   120 if st<>0 then print "status " + str$(st)
   122 get#2,c$:if c$="" goto 122
   130 if st=8 goto 120
   131 if asc(c$)=13 goto 150:rem start of corrupt char fixes
   132 if asc(c$)>=192 and asc(c$)<=223 then c$=chr$(asc(c$)-96)
   133 if asc(c$)>=97 and asc(c$)<=122 then c$=chr$(asc(c$)-32)
   134 if asc(c$)>=176 and asc(c$)<=185 then c$=chr$(asc(c$)-128)
   135 if asc(c$)=168 then c$="t"
   136 if asc(c$)=172 then c$=","
   137 if asc(c$)=162 then c$="q"
   138 if asc(c$)=185 then c$="a"
   139 if asc(c$)=182 then c$="v"
   140 if asc(c$)=178 then c$="r"
   141 if asc(c$)=174 then c$="n"
   142 ur$=ur$+c$
   143 goto 120
   150 goto 61000
   1000 rem print record
   1001 a$=fl$:ma=10:sl$=",":cn=1
   1002 gosub 59012:rem split record values for printing
   1003 for k=1 to wd
   1004 print str$(k) + ": " + mid$(vl$, cn, val(wd$(k))) + " ";
   1005 cn=cn+val(wd$(k)):next:print
   1006 return
   59010 rem string splitter, splits twice by default
   59011 ma=3:sl$=" ":rem splitter default settings
   59012 for i=0 to ma: wd$(i)="": next: wd=1
   59013 for i=1 to len(a$)
   59015 wd$(0)=mid$(a$,i,1)
   59017 if wd$(0)=sl$ and wd<>ma then wd=wd+1: next
   59019 wd$(wd)=wd$(wd)+wd$(0): next
   59022 return
   59050 rem replace question mark as input prompt
   59052 poke 52, 48: poke 56, 48
   59053 ug=12288:cg=53248
   59054 poke 56334, peek(56334) and 254
   59055 poke 1, peek(1) and 251
   59056 for k=1 to 2047
   59057 poke ug+k, peek(cg+k)
   59058 next
   59059 poke 1, peek(1) or 4
   59060 poke 56334, peek(56334) or 1
   59061 poke 53272, (peek(53272) and 240)+12
   59062 for j=0 to 7:read a: poke ug+8*63+j, a:next j
   59064 data 000, 000, 056, 124, 126, 254, 048, 000
   59065 return
   60000 rem command dispatch
   60001 rem print cm$:rem echo command
   60002 a$=cm$
   60003 gosub 59010:rem split command
   60004 if wd$(1)="quit" goto 60100
   60005 if ep$<>"" and mid$(wd$(1),1,len(ep$))<>ep$ goto 20
   60006 if wd$(1)="query" goto 60105
   60007 if wd$(1)="update" goto 60120
   60008 if wd$(1)="search" goto 60130
   60009 goto 20
   60100 rem quit command
   60101 end
   60105 rem query command
   60106 print "doing a query"
   60107 print#2,"query:" + wd$(2) + " " + wd$(3) + chr$(0);
   60108 ep$="query"
   60109 goto 100
   60120 rem update command
   60121 print "doing an update"
   60122 print#2,"update:" + wd$(2) + " " + wd$(3) + chr$(0);
   60123 ep$="update"
   60124 goto 100
   60130 rem search command
   60131 print "doing a search"
   60132 print#2,"search:" + wd$(2) + " " + wd$(3) + chr$(0);
   60133 ep$="search"
   60134 goto 100
   61000 rem response dispatch
   61001 rem print "response " + ur$:rem echo response
   61002 a$=ur$
   61003 gosub 59010:rem split command
   61004 if wd$(1)="quit" goto 60100
   61005 if ep$="" then return:rem if we are not expecting a response, ignore
   61006 if wd$(1)="query" or wd$(1)="search" goto 61105
   61007 if wd$(1)="update" goto 61305
   61008 goto 100
   61105 rem query response
   61107 if wd$(2)="count" goto 61220
   61108 if wd$(2)="fields" goto 61240
   61109 if wd$(2)="record" goto 61230
   61110 if wd$(2)="error" goto 61250
   61111 if wd$(2)="done" goto 20
   61120 goto 100
   61220 rem get ready for query/search response
   61221 ri=1:gosub 16
   61223 goto 61120
   61230 rem query/search record handler
   61231 print chr$(18) + chr$(ri+64) + chr$(146) + ": ";
   61232 rc$(ri)=wd$(3):ri=ri+1
   61233 a$=wd$(3):ma=2:sl$=" "
   61234 gosub 59012:rem split record parts for printing
   61235 fl$=wd$(1):vl$=wd$(2)
   61236 gosub 1000
   61239 goto 61120
   61240 rem query fields handler
   61241 a$=wd$(3):ma=10:sl$=" "
   61242 gosub 59012:rem split object name and field names
   61243 print wd$(1)
   61244 for j=2 to wd: print str$(j-1) + ": " + wd$(j) spc(2);:next:print
   61249 goto 61120
   61250 print "query error: " + wd$(3)
   61259 goto 20
   61305 rem update response
   61307 if wd$(2)="error" goto 61350
   61308 if wd$(2)="done" goto 20
   61350 print "update error: " + wd$(3)
   61359 goto 20
