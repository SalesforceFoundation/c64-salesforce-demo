;From http://www.lemon64.com/forum/viewtopic.php?t=36491&sid=0c9db642484183b7b07bf8d768f056c8

;Koala Picture Code by Stranger on CSDb 
PICTURE = $2000 
BITMAP = PICTURE 
VIDEO = PICTURE+$1f40 
COLOR = PICTURE+$2328 
BACKGROUND = PICTURE+$2710 

*=$0801 
; BASIC stub: "1 SYS 2061" 
!by $0b,$08,$01,$00,$9e,$32,$30,$36,$31,$00,$00,$00 

JMP $5000 
* = $5000 
sei 
lda #$00 
sta $d020 ; Border Color 
lda BACKGROUND 
sta $d021 ; Screen Color 

; Transfer Video and Color 
ldx #$00 
.LOOP 
; Transfers video data 
lda VIDEO,x 
sta $0400,x 
lda VIDEO+$100,x 
sta $0500,x 
lda VIDEO+$200,x 
sta $0600,x 
lda VIDEO+$2e8,x 
sta $06e8,x 
; Transfers color data 
lda COLOR,x 
sta $d800,x 
lda COLOR+$100,x 
sta $d900,x 
lda COLOR+$200,x 
sta $da00,x 
lda COLOR+$2e8,x 
sta $dae8,x 
inx 
bne .LOOP 
; 
; Bitmap Mode On 
; 
lda #$3b 
sta $d011 
; 
; MultiColor On 
; 
lda #$d8 
sta $d016 



;Wait Code by PeteD on Lemon64 
lda #$18 
sta $d018 
         ldx #60*3  ;60 fps * 3 seconds 
         lda #128 
loop1 cmp $d012     ;check if the raster has reached line 128 
         bne loop1  ;no, so keep checking 
loop2 cmp $d012     ;if it has you want to make sure you dont catch it more than once per frame 
         beq loop2  ;so wait till it isn't 0 any more 
         dex 
         bne loop1  ;loop round 60*3 times 
          
;File must be at same directory ofcourse 

* = $1ffe 
!binary "resources/qtlfu_ko_fs.koala",,0 
