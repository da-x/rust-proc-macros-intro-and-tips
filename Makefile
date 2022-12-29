REV=./node_modules/.bin/reveal-md slides.md --css custom.css

all:
	yarn install
	$(REV) --static _site

deploy:
	yarn install
	$(REV) --static _site
	rm -rf .git/deploy/*
	mv _site/* .git/deploy/
	rmdir _site

	cd .git/deploy && git add -f .
	cd .git/deploy && gsr _assets\///assets\/ -f
	cd .git/deploy && git add -f .
	cd .git/deploy && (git commit -a -m "Update" || true)
	cd .git/deploy && git push -f origin HEAD:gh-pages

test:
	python test.py

serve:
	$(REV) -w
