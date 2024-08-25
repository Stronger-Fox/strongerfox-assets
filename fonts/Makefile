.PHONY: all clean

FONT ?= ruth-calligraph
TEXT ?= Stronger Fox
OUTPUT ?= sfoxn.woff2


FONTDIR = $(FONT)-font
FONTFILE = $(wildcard $(FONTDIR)/*.ttf)

all: build/$(OUTPUT)

build/$(OUTPUT): $(FONTFILE) build/
	@echo 'Processing "$(FONTFILE)" ...'
	poetry run pyftsubset "$<" --output-file="$@" \
		--verbose --flavor=woff2 --text="$(TEXT)" --no-notdef-glyph --name-IDs=""
	@echo -e "Output: $@\t($$(stat -c '%s' $@ | numfmt --format %.2f --to=iec)B)"

build/:
	mkdir $@

poetry.lock: pyproject.toml
	poetry update

clean:
	-rm -rf build/
	-rm -f poetry.lock
