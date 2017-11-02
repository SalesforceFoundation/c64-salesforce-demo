!zone macros

!macro set16im .value, .dest {                                   ; store a 16bit constant to a memory location
    lda #<.value
    sta .dest
    lda #>.value
    sta .dest+1
}
