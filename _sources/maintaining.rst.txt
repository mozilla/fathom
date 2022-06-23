===========
Maintaining
===========

A successful production ruleset will need to be improved from time to time.

Reviewing a Change
==================

Points to consider when reviewing a model change:

* Make sure the metrics are better. If the change involved adding samples, do a :doc:`fathom test<commands/test>` run with the old coefficients (and the new samples) as a baseline. This should result in worse metrics than the production ruleset, since you made it harder by introducing failing samples. Then compare those metrics to a new :doc:`fathom train<commands/train>` run with the new samples and any ruleset code changes. If the second metrics are better, you should adopt the new model. See :ref:`Evaluating Metrics <evaluating-metrics>` for how to compare them.

  Ideally you can collect several samples representative of the problem you're trying to solve and distribute them across the training/validation/test sets. If you can find only one, you'll have to settle for putting it in training so the coefficients can be informed by it.
* Make sure the "before" and "after" metrics, with commandline flags, are in the commit message to justify the change.
* Review ruleset code changes as in a normal code review, for correctness and comprehensibility.

If Adding Samples
-----------------

If you added samples to the corpus, do these as well:

* Make sure the names of the samples conform to the convention documented in ``samples/rubric.txt``.
* Check that the samples have been :doc:`extracted<commands/extract>` and render properly in Firefox. Use :doc:`fathom serve<commands/serve>` to make sure cross-origin policies (which are picky for ``file://`` URLs) aren't preventing the loading of subresources. Improper rendering can cause improper training.
