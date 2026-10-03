PYTHON ?= python3
CA65 ?= ca65
LD65 ?= ld65

BUILD := build
ROM := $(BUILD)/nes-sdr.nes
OBJ := $(BUILD)/main.o
CHR := $(BUILD)/spectrum.chr

.PHONY: all clean

all: $(ROM)

$(BUILD):
	mkdir -p $(BUILD)

$(CHR): | $(BUILD)
	$(PYTHON) ../tools/render_mock.py --out $(CHR)

$(OBJ): src/main.s $(CHR) | $(BUILD)
	$(CA65) src/main.s -o $(OBJ)

$(ROM): $(OBJ) nes.cfg
	$(LD65) -C nes.cfg $(OBJ) -o $(ROM)
	@echo "built $(ROM)"

clean:
	rm -rf $(BUILD)
