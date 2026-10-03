.setcpu "6502"

PPUCTRL   = $2000
PPUMASK   = $2001
PPUSTATUS = $2002
PPUADDR   = $2006
PPUDATA   = $2007

.segment "HEADER"
.byte $4e, $45, $53, $1a
.byte 2                  ; 32 KiB PRG
.byte 1                  ; 8 KiB CHR
.byte $00                ; mapper 0, horizontal mirroring
.byte $00
.res 8, $00

.segment "CODE"

.proc wait_vblank
@wait:
    bit PPUSTATUS
    bpl @wait
    rts
.endproc

.proc reset
    sei
    cld
    ldx #$40
    stx $4017
    ldx #$ff
    txs
    inx
    stx PPUCTRL
    stx PPUMASK
    stx $4010

    jsr wait_vblank
    jsr wait_vblank

    ; Palette at $3F00.
    bit PPUSTATUS
    lda #$3f
    sta PPUADDR
    lda #$00
    sta PPUADDR
    ldx #$00
@palette:
    lda palette, x
    sta PPUDATA
    inx
    cpx #$20
    bne @palette

    ; Fill nametable 0 with tile 248 (blank).
    bit PPUSTATUS
    lda #$20
    sta PPUADDR
    lda #$00
    sta PPUADDR
    lda #248
    ldx #$00
    ldy #$04
@fill_page:
    sta PPUDATA
    inx
    bne @fill_page
    dey
    bne @fill_page

    ; Place graph tiles 0..247 at rows 11..18, columns 0..30.
    ; Nametable address = $2000 + 11*32 = $2160.
    bit PPUSTATUS
    lda #$21
    sta PPUADDR
    lda #$60
    sta PPUADDR

    ldx #$00              ; tile number
    ldy #$08              ; eight tile rows
@graph_row:
    lda #$1f              ; 31 graph columns
    sta $00
@graph_col:
    txa
    sta PPUDATA
    inx
    dec $00
    bne @graph_col
    lda #248              ; final column blank
    sta PPUDATA
    dey
    bne @graph_row

    ; Clear attributes ($23C0-$23FF) to palette 0.
    bit PPUSTATUS
    lda #$23
    sta PPUADDR
    lda #$c0
    sta PPUADDR
    lda #$00
    ldx #$40
@attr:
    sta PPUDATA
    dex
    bne @attr

    lda #%10000000        ; enable NMI, pattern table 0
    sta PPUCTRL
    lda #%00001010        ; show background, including left edge
    sta PPUMASK

@forever:
    jmp @forever
.endproc

.proc nmi
    rti
.endproc

.proc irq
    rti
.endproc

.segment "RODATA"
palette:
.byte $0f,$30,$21,$11,  $0f,$00,$00,$00
.byte $0f,$00,$00,$00,  $0f,$00,$00,$00
.byte $0f,$16,$27,$38,  $0f,$00,$00,$00
.byte $0f,$00,$00,$00,  $0f,$00,$00,$00

.segment "VECTORS"
.word nmi
.word reset
.word irq

.segment "CHR"
.incbin "build/spectrum.chr"
