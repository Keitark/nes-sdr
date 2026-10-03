.setcpu "6502"

PPUCTRL   = $2000
PPUMASK   = $2001
PPUSTATUS = $2002
PPUADDR   = $2006
PPUDATA   = $2007

RAM_WAIT  = $0200

.segment "HEADER"
.byte $4e, $45, $53, $1a
.byte 2                  ; 32 KiB PRG
.byte 1                  ; 8 KiB CHR
.byte $00                ; mapper 0, horizontal mirroring
.byte $00
.res 8, $00

.segment "ZEROPAGE"
nt_ptr: .res 2

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
    stx $4017            ; inhibit APU frame IRQ
    ldx #$ff
    txs
    inx
    stx PPUCTRL          ; rendering/NMI off while setting up
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

    ; Copy 960-byte fixed UI nametable to $2000.
    bit PPUSTATUS
    lda #$20
    sta PPUADDR
    lda #$00
    sta PPUADDR

    lda #<ui_nametable
    sta nt_ptr
    lda #>ui_nametable
    sta nt_ptr+1

    ldx #$03             ; three complete 256-byte pages
@nt_page:
    ldy #$00
@nt_page_byte:
    lda (nt_ptr), y
    sta PPUDATA
    iny
    bne @nt_page_byte
    inc nt_ptr+1
    dex
    bne @nt_page

    ldy #$00             ; final 192 bytes
@nt_tail:
    lda (nt_ptr), y
    sta PPUDATA
    iny
    cpy #$c0
    bne @nt_tail

    ; Clear attributes ($23C0-$23FF) to palette 0.
    lda #$00
    ldx #$40
@attr:
    sta PPUDATA
    dex
    bne @attr

    ; Background pattern table 0, NMI deliberately disabled.
    lda #%00000000
    sta PPUCTRL
    lda #%00001010       ; show background, including left edge
    sta PPUMASK

    ;
    ; Critical zero-mod live-refresh trick:
    ; copy an infinite loop into the 2A03's internal RAM and execute there.
    ; From this point onward the CPU makes no cartridge PRG reads, so the
    ; ESP32 may safely assert ROM Vomitter LOAD and take both SRAM buses.
    ;
    ldx #$00
@copy_ram_wait:
    lda ram_wait_code, x
    sta RAM_WAIT, x
    inx
    cpx #(ram_wait_end - ram_wait_code)
    bne @copy_ram_wait

    jmp RAM_WAIT
.endproc

ram_wait_code:
    jmp RAM_WAIT
ram_wait_end:

.proc nmi
    rti
.endproc

.proc irq
    rti
.endproc

.segment "RODATA"
palette:
.byte $0f,$30,$16,$27,  $0f,$00,$00,$00
.byte $0f,$00,$00,$00,  $0f,$00,$00,$00
.byte $0f,$16,$27,$38,  $0f,$00,$00,$00
.byte $0f,$00,$00,$00,  $0f,$00,$00,$00

ui_nametable:
.incbin "build/nametable.bin"

.segment "VECTORS"
.word nmi
.word reset
.word irq

.segment "CHR"
.incbin "build/spectrum.chr"
