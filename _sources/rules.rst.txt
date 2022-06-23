=============
Writing Rules
=============

Once you've collected some training samples, you can begin to write rules.

The Language
============

Think of Fathom as a tiny programming language that recognizes the significant parts of DOM trees by means of its programs, Fathom rulesets. A ruleset is an unordered bag of rules, each of which takes in a DOM node and annotates it with a score, type, or note to influence future rules. At the end of the chain of rules, out pop one or more pieces of output—typically high-scoring nodes of certain types—to inform the surrounding imperative program. You'll also see the term :term:`fnode` used. Standing for "Fathom node", it is a wrapper around a DOM node that is used for Fathom bookkeeping.

This is an excerpt from a ruleset that finds whole-page translucent overlays behind pop-ups. It combines a variety of signals to score DOM nodes according to how likely they are to be overlays:

.. code-block:: js

    import {ruleset, rule, dom, type, score, out, utils} from 'fathom-web';
    const {isVisible, linearScale} = utils;

    const rules = ruleset([
        // Consider all <div> tags as candidate overlays:
        rule(dom('div'), type('overlay')),

        // Contribute the "bigness" of the node to its overlay score:
        rule(type('overlay'), score(big), {name: 'big'}),

        // Contibute the opacity of the node to its overlay score:
        rule(type('overlay'), score(nearlyOpaque), {name: 'nearlyOpaque'}),

        // Contribute some other signals as well:
        rule(type('overlay'), score(monochrome), {name: 'monochrome'}),
        rule(type('overlay'), score(suspiciousClassOrId), {name: 'classOrId'}),
        rule(type('overlay'), score(isVisible), {name: 'visible'}),

        // Offer the max-scoring overlay-typed node under the output key
        // "overlay". The score on that node will represent the probability,
        // informed by a corpus of training samples, that the node is, indeed,
        // a pop-up overlay.
        rule(type('overlay').max(), out('overlay'))
    ]);

    /**
     * Return whether the passed-in div is the size of the whole
     * viewport/document or nearly so.
     */
    function big(fnode) {
        // Compare the size of the fnode to the size of the viewport. Spot-
        // checking the training set shows the overlay is never the size of the
        // whole document, just the viewport.
        const rect = fnode.element.getBoundingClientRect();
        const hDifference = Math.abs(rect.height - window.innerHeight);
        const wDifference = Math.abs(rect.width - window.innerWidth);

        // Compress the result into the 0..1 range. 250px is getting into "too
        // tall to just be nav or something" territory.
        return linearScale(hDifference + wDifference, 250, 0);
    }

    function nearlyOpaque(fnode) {...}
    function monochrome(fnode) {...}
    function suspiciousClassOrId(fnode) {...}

Your rulesets go in a file called ``rulesets.js`` next to your ``samples`` folder. The unabridged :doc:`example` is in the appendix, and you should pattern yours after it.

Dataflow
--------

Fathom is a `dataflow language <https://en.wikipedia.org/wiki/Dataflow_programming>`_. Each rule is shaped like ``rule(left-hand side, right-hand side)``. The *left-hand side* (LHS) pulls in one or more DOM nodes as input: either ones that match a certain CSS selector (:func:`dom()`) or ones tagged with a certain type by other rules (:func:`type()`). The *right-hand side* (RHS) then decides what to do with those nodes:

* Adding a :func:`score`. This is the most common action; it drives Fathom's recognition of entities.
* Assigning an additional :func:`type`
* Scribbling a :func:`note` on it. Notes let you avoid repeated computation and attach additional information to output nodes.
* Or some combination thereof

Envision the rule as a pipeline, with the DOM flowing in one end, nodes being picked and passed along to RHSs which twiddle them, and then finally falling out right side, where they might flow into other rules whose LHSs pick them up. It's a slithering sort of flow.

This rule, which takes in :term:`fnodes<fnode>` that have previously been identified as text containers and adds a word-count annotation... ::

    rule(type('textContainer'), type('countedWords').note(fnode => fnode.element.textContent.split(/\s+/).length))

...can be thought of as...

.. code-block:: none

    textContainer fnodes emitted       assign "countedWords" type and
         from other rules         ->   a note containing word count    ->  changed nodes ─╮
                                                                                          │
    ╭─────────────────────────────────────────────────────────────────────────────────────╯
    │
    │
    ╰─>  other rules' LHSs        ->   ...                             ->   ...

Remember that Fathom's rulesets are unordered, so any rule's output can flow into any other rule, not just ones that happen to come lexically after it.

Starting Your Ruleset
=====================

Begin your own ruleset by copying and pasting the :doc:`example`. It illustrates the API you need to follow to hook into the trainer, namely the ``trainees`` object and its fields. As you are writing your ruleset, refer to the :doc:`ruleset` API documentation as well for the full list of routines you can use. You can also visit the :doc:`zoo` for inspiration.

Designing Rules
===============

Each rule should generally express one machine-learning feature—or "smell", to coin a metaphor. The score it applies—the return value of the callback passed to :func:`score`—should be a number between 0 and 1, inclusive, representing the probability that that smell is present. These smells are later balanced by the trainer.

.. note::

   For many smells, it's natural to return hard 0s or 1s (or trues and falses, if that's more convenient). If you have fuzzier values to return—as from a rule that expresses something subjectively defined like "image is big"—:func:`linearScale` and :func:`sigmoid` will help you clamp down extreme values. Make the choice based on whether two adjacent extreme values should still have distinguishable outputs. If they should, go with sigmoid().

Sources of Signal
-----------------

What sorts of rules should you write? In short, ones that express simple, atomic smells that tend to be found in—or lacked by—target elements. For example, if you are trying to recognize the images of products for sale on shopping sites, the target image might have smells like...

* Large size
* Position near the top of the page
* Position near the left of the page
* IDs or class names that contain the strings "hero" or "product"

Don't worry about expressing boolean combinations of smells except as a last resort. It's generally sufficient to let Fathom optimize a linear combination of them. Also, Fathom will determine on its own whether to give a positive or negative weight to a smell; you don't need to tell it.

Since the primitives exposed by Fathom are thus far geared to the measurement of DOM properties (rather than, say, natural language processing), the best bang for your buck is generally rules that consider...

* CSS classes and IDs. Begin by simply testing for inclusion of signal-bearing strings. It is probably unnecessary to apply tokenization.
* Rendered size or position of elements
* Alignment or proximity of elements to each other. So far, the state of the art is to program a bit of "look around" into the scoring callback. It is also possible to get ahold of the :class:`BoundRuleset` object and try to pair up the examined node with another of a certain type, but so far it's a manual process.
* Font sizes
* Colors and borders
* Visibility
* Any of the above in :func:`ancestor<ancestors>` elements of the target

A useful technique is to look at some of the pages in your corpus and blur your eyes slightly. This shows you the page as Fathom sees it: you can't read the text, but you can likely still recognize the target elements. Write rules that express the hints you are using to do so.

Computed CSS properties are worth a special mention: `getComputedStyle() <https://developer.mozilla.org/en-US/docs/Web/API/Window/getComputedStyle>`_ is the most robust way to retrieve style information about an element, since most properties are inherited through the complex interplay of stylesheets. Don't try to look at ``style`` attributes directly or otherwise painstakingly reason out styles.

Rules of Thumb
--------------

* Lots of simple rules are better than fewer, more complex ones. Not only are they easier to write, but the further you can break up your guesses into separately optimizable pieces, the more good the trainer can do.
* Your rules don't all have to be good. If you have an idea for a smell, code it up. If it was a bad idea, the trainer will likely give it a coefficient near 0, and you can prune it away.
* :func:`when()` is good for early pruning: hard, yes/no decisions on what should be considered. Scores are for gradations. Pruning makes your vector files smaller and training faster.
* Many good rule ideas come out of labeling samples. If you are not labeling samples yourself, at least study them in depth so you can notice patterns.

Getting Ready to Train
======================

Once you've written a few scoring rules, it's time for :doc:`training`. This computes optimal weighting coefficients and biases, which let the ruleset compute accurate confidences of its decisions. Be sure to write at least 2 rules before attempting to train; when there's only one, the trainer has nothing to balance.
