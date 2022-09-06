REV=./node_modules/.bin/reveal-md slides.md --css custom.css

all:
	yarn install
	$(REV) --static _site

serve:
	$(REV) -w
