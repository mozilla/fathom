===========
Development
===========

Source
======

It's on `GitHub <https://github.com/mozilla/fathom>`_.

Tests and Examples
==================

To run the tests, run... ::

    make lint test

This will also run the linter and analyze test coverage. To render the coverage report human-legibly, run ``make coverage``. You can then find the coverage report in the ``coverage`` directory.

You can also run the linter or tests for just one subproject at a time. For example, to test the CLI tools... ::

    cd cli
    make lint test

If you want to drop into the debugger in the middle of a JS test, add a ``debugger;`` statement at your desired breakpoint, then run ``make debugtest`` in the ``fathom`` subproject::

    cd fathom
    make debugtest

Docs
====

To build the docs... ::

    make docs

Gotchas
=======

If you are developing the CLI tools and your changes to their embedded copy of the Fathom JS framework don't seem to be taking effect, commit first. The make target that builds ``fathom.zip`` uses ``git archive`` to pull from ``HEAD``. In this scenario, we tend to use a single local commit we amend with ``git commit --amend --no-edit`` when we want to test our changes.

Windows Considerations
======================

Fathom uses `makefiles <https://www.gnu.org/software/make/manual/make.html>`_ to do its builds and run its tests. These makefiles rely on Unix commands. Therefore, if you are developing on Windows, you need access to these Unix commands through something like `Cygwin <https://www.cygwin.com/>`_. You can build and test Fathom using `Windows Subsystem for Linux <https://docs.microsoft.com/en-us/windows/wsl/>`_, but just know that you are technically building and testing Fathom in Linux when you do.

Future Roadmap
==============

Fathom 3.x: the incremental gains
---------------------------------

* Regularization. Overfitting doesn't generally happen much, if you keep your eyes on the Tensorboard graphs to dodge wrong LRs, but sometimes you can still add signal to the model and get worse accuracy as a result. That should never happen. Regularization might help with that.
* Automatic normalization. Right now, it's the ruleset author's responsibility to keep scoring callback outputs between 0 and 1. There are helpers to scale things linearly and sigmoidally, but it would be great to do this intelligently and automatically in the trainer, informed by the corpus rather than having the dev make guesses or painstaking calculations about the distribution.
* Shuffle every iteration. Might help avoid overfitting. We shuffle once now.
* Learn cutoff values. Sometimes there are values that, <7, should be treated one way and >7 another. We've had to model these by hand so far, but this should be automatic. We could using bucketing or deeper NNs, but we probably need much bigger corpora to support deeper NNs. The trainer already supports deeper NNs, but the client code needs support, and that'll be a breaking change because the format of the coefficients and biases will have to expand. The math itself, of course, is trivial.
* Make corpus collection cheaper. Another theme for the future, related to the above, is making training data much cheaper to collect, because that would let us trade skilled labor of rule creation for unskilled corpus collection.
* Text signal. So far, we mostly pay attention to markup. Any body-text stuff has to be implemented by the ruleset author. There's no reason we can't integrate a Bayesian (or other) text model on body text or even tokenized CSS classes and IDs. Or URL segments. Or other attribute values. A Bayesian classifier could happily live as a scoring callback, though the trainer would have to be special-cased to go do a separate pass to collect bag-of-words numbers, then in the main pass hand that to the Bayesian scoring callbacks and let the NNs balance the outputs of them as usual. But at this point, I prefer putting effort toward Fathom 4 than this fairly expensive effort with much overlap.
* Visualization. It would be great to have a visualization tool that would show, on sample pages, what's getting classified right and wrong. Just haven't got around to it. Not hard.

Fathom 4: the great beyond
--------------------------

We had perf problems using Fathom for the FF Companion: running it on every page or several times per page. I've never done much optimization, though profiling shows that 80% of time is spent on DOM calls. DOM calls are both slow and block the main thread, and the DOM cannot be moved off the main thread to do recognition concurrently. So I took a few afternoons and said "What if we dispense with all the DOM calls, then?" Reader Mode just throws the markup across thread boundaries. Let's see what we can get out of that. Sure, we lose heights and widths and visibilities and positions on the page, but there's still lots of signal in that thar text, and Fathom 1 started out there, as a node app running against a stub DOM implementation without access to a renderer. To make a long story short, I build a whole-page categorizer using logistic regression on TFIDF'd bags of words, with all markup stripped out, and...

* It gives 85% testing accuracy, very comparable with Smooth Shopping's 90% *validation* accuracy.
* It took a month or more to write the Shopping ruleset. This one I didn't have to write at all; it was trained in 5 seconds.
* I didn't engineer a single feature for this. Not so much as a price regex. It's a general classifier. It did similarly well against our hand-rolled Smoot Article recognizer, which is especially interesting since Articles have wider subject matter than shopping pages.
* There's tons of signal still left on the floor:
    * Stemming. Tried it but didn't have an obvious impact. Odd. Try again.
    * All the markup. I stripped out everything but body text. Teach it to use tag names, CSS classes, IDs, and URL segments.

What's a more open question is whether this can be adapted from whole-page categorization to element recognition, like Fathoms 1-3, which is the more major case.

* Continue with this bag-of-words approach on a pruned down set of candidate tags, statistically informed? Either algorithmically come up with a minimal querySelector arg, or use a compressed model to predict which tags we ought to examine, like an attention system in computer vision.
* Perhaps add some hand-rolled but still generic signals, like innertext length, markup bits, or consideration of surrounding elements (parents, grandparents, siblings, etc.).

If this could work, it would be a game-changer. Just as Fathoms 1-3 let us do something we couldn't do before at all, Fathom 4 would let you do it in a couple afternoons of low-skilled work rather than a couple weeks to months of skilled.