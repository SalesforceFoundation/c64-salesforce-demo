;Based on http://dustlayer.com/c64-coding-tutorials/2013/4/8/episode-2-3-did-i-interrupt-you 

BORDERAD = $d020
; We want to flash that green money color
FLASHCOL = 5
UNFLCOL = 14

; number of jiffies we want to wait
FLASHDEL = 40
; number of jiffies/256 we want to wait
SOUNDDEL = 2

; Autorun on load
* = $0801                               ; BASIC start address (#2049)
!byte $0d,$08,$dc,$07,$9e,$20,$34,$39   ; BASIC loader to start at $c000...
!byte $31,$35,$32,$00,$00,$00           ; puts BASIC line 2012 SYS 49152
* = $c000                               ; start address for 6502 code


           ; Open the serial connection
           jsr rs232_open

           ; Clear a timer storage space for the music
           lda #0
           sta $cffd

           ; Set up the irq override
           sei         ; set interrupt disable flag
            
           ldy #$7f    ; $7f = %01111111
           sty $dc0d   ; Turn off CIAs Timer interrupts
           sty $dd0d   ; Turn off CIAs Timer interrupts
           lda $dc0d   ; cancel all CIA-IRQs in queue/unprocessed
           lda $dd0d   ; cancel all CIA-IRQs in queue/unprocessed
          
           lda #$01    ; Set Interrupt Request Mask...
           sta $d01a   ; ...we want IRQ by Rasterbeam

           lda #<irq   ; point IRQ Vector to our custom irq routine
           ldx #>irq 
           sta $314    ; store in $314/$315
           stx $315   

           lda #$00    ; trigger first interrupt at row zero
           sta $d012

           lda $d011   ; Bit#0 of $d011 is basically...
           and #$7f    ; ...the 9th Bit for $d012
           sta $d011   ; we need to make sure it is set to zero 

           cli         ; clear interrupt disable flag
           ; Done setting up the irq override
           jmp *       ; infinite loop


irq        dec $d019        ; acknowledge IRQ

           ; see if we are already in a flash
           lda BORDERAD
           and #15
           cmp #FLASHCOL
           beq chkstopit ; if so, should we stop?
           bne chkserial ; if not, should we start?

done       jsr $f69b ; increment clock
           jsr $579a ; play music for this irq run
           jmp $ea81 ; return to kernel interrupt routine

chkserial  jsr rs232_try_read_byte ; look for byte in serial port
           cmp #0
           bne bkgdon ; we should start
           jmp done

bkgdon     lda $a2 ; bring in system timer value
           sed ; do decimal math
           adc #FLASHDEL ; add the configured delay 
           sta $cfff ; store the time at which we want to stop the flash

           ; change the color
           lda #FLASHCOL
           sta BORDERAD

           ; should we start the sound?
           lda $a1 ; bring in a different byte for the sound timer
           cmp $cffd ; have we ever started the sound, or is it time to start it again?
           bcs soundon ; if $a1 >= $cffd, start the sound
           jmp done

soundon    jsr $5597 ; run the init code for the sid sound file
           lda $a1 ; set up system timer value for sound
           sed ; do decimal math
           adc #SOUNDDEL ; add the configured delay
           sta $cffd ; store the time at which it's ok to restart the music
           jmp done

bkgdoff    lda #0
           sta $cfff ; Clear the byte that holds the flash end time

           ; change the color
           lda #UNFLCOL
           sta BORDERAD
           jmp done

chkstopit  lda $a2
           cmp $cfff ; is the system time past the flash stop time?
           bcs bkgdoff ; if $a2 >= $cfff
           jmp done

* = $558c
!bin "resources/music.sid",,$7c+2
