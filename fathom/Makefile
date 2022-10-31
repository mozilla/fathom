PATH := ./node_modules/.bin:$(PATH)

JS  := $(shell find . -name '*.mjs' | grep -v '^./node_modules/.*' | sed 's/\.mjs/\.js/')
MJS := $(shell find . -name '*.mjs' | grep -v '^./node_modules/.*')

# It's faster to invoke Babel once and compile everything than to invoke it
# separately on even 2 individual files that changed.
%.js: %.mjs .npm_installed .babelrc; @node_modules/.bin/babel *.mjs **/*.mjs --out-dir . --relative

js: $(JS)

lint: .npm_installed
	@node_modules/.bin/eslint --ext mjs .
	@node_modules/.bin/eslint test/browser

test: $(JS) .npm_installed
	@node_modules/.bin/nyc --reporter=text-summary node_modules/mocha/bin/_mocha --recursive

coverage: .npm_installed test
	@node_modules/.bin/nyc report --reporter=html

coveralls: .npm_installed
	node_modules/.bin/nyc report --reporter=text-lcov | coveralls

debugtest: $(JS) .npm_installed
	# This is known to work on node 7.6.0.
	@node_modules/.bin/mocha --inspect-brk

publish: $(JS)
	cp ../LICENSE ./
	cp ../README.md ./
	npm publish

bundle: dist/fathom.js

bundleESModule: dist/fathom.mjs

# .npm_installed is an empty file we touch whenever we run npm install. This
# target redoes the install if package.json is newer than that file:
.npm_installed: package.json
	npm install
	touch $@

clean:
	rm -rf $(JS) node_modules .npm_installed LICENSE README.md


# Private targets:

dist/fathom.js: rollup.config.js .npm_installed $(MJS)
	@node_modules/.bin/rollup -c

dist/fathom.mjs: rollupESModule.config.js .npm_installed $(MJS)
	@node_modules/.bin/rollup -c rollupESModule.config.js


.PHONY: js lint test coveralls debugtest publish bundle clean
