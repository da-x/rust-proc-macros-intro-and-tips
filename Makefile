REV=./node_modules/.bin/reveal-md slides.md --css custom.css

all:
	yarn install
	$(REV) --static _site

test:
	python test.py

serve:
	$(REV) -w
