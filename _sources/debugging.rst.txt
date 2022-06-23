=========
Debugging
=========

Setting Breakpoints
===================

If the :doc:`trainer<training>` reports JavaScript errors, you've probably got a bug in your ruleset code. If you can't find it by examination and need to place a breakpoint, the tool of choice is the FathomFox Evaluator.

#. Run :doc:`fathom fox<commands/fox>`, and pass it your ruleset::

    fathom fox -r rulesets.js

#. Use the instance of Firefox that comes up to open a page that you think will reproduce the problem.
#. Show the dev tools, and navigate to the Debugger panel.
#. In the disclosure tree to the left, disclose FathomFox, and select `rulesets.js`.
#. Scroll to the bottom, past the minified mess, and you’ll see your ruleset code. Place a breakpoint as you like, probably in one of your scoring callbacks.
#. Invoke the Evaluator from the Fathom toolbar menu.
#. Click Evaluate to run the ruleset over the loaded tabs.

You’ll end up in the debugger, paused at your breakpoint.

Identifying Misrecognized Elements
==================================

.. note::
   Make sure you have the latest trained coefficients and biases pasted into your ruleset before you do this, or recognition won't work well.

FathomFox's Evaluator can point out misrecognized elements, in case the tag exerpts emitted by the trainer are insufficient to identify them. To use the Evaluator:

#. Open an instance of Firefox with FathomFox and your ruleset loaded (``fathom-fox -r rulesets.js`` makes this simple).
#. Open all of the samples you want to diagnose as separate tabs.
#. Open the Evaluator page using FathomFox's browser action button.
#. In the Trainee dropdown, select the trainee you want to diagnose.
#. Click the Evaluate button.
#. Click any red box to navigate to a page with misrecognized nodes.
#. On that tab, open the dev tools panel (ctrl-shift-N) and switch to the Fathom panel. Unfortunately, there aren't yet web extension APIs to do this part automatically.
#. At this point, you’ll see a quick and dirty representation of the “bad” element: a new label called “BAD [the trainee]”. Be sure to delete this if you choose to re-save the page for some reason. Also note that the BAD label is created only when the bad cell is clicked, for speed; if you navigate to the bad page manually, the label won’t be there, or there might be an old label from a previous iteration.
#. Return to the Evaluator tab and click any other red boxes you want to explore.

Histograms
==========

Finally, a great way to examine the scores your rules are emitting is :doc:`fathom histogram<commands/histogram>`. It can show you how useful a discriminator a rule is and help you notice when the distribution of output values is not what you expect.

.. image:: img/histogram.png
