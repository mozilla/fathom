========
Training
========

Training is the process by which Fathom combines your handwritten rules with your labeled example pages to create the most accurate possible recognizer. Training emits a set of numerical parameters:

* One *coefficient* per rule, which indicates the rule's relative weight
* One *bias* per type, which centers element's scores so they can be construed as 0..1 confidences

Running the Trainer
===================

.. note::

   Fathom has had several trainers over its evolution. Both the Corpus Framework and the trainer built into old versions of FathomFox are obsoleted by :doc:`fathom train<commands/train>`, described herein.

Once your samples are collected and at least several rules are written, you're ready to do some initial training. Training is done for one type at a time. If you have types that depend on other types (an advanced case), train the other types first.

Run the trainer. A simple beginning, using just a training set, is... ::

    fathom train samples/training --ruleset rulesets.js --trainee yourTraineeId

...yielding something like... ::

    {"coeffs": [
            ['nextAnchorIsJavaScript', 1.1627885103225708],
            ['nextButtonTypeSubmit', 4.613410949707031],
            ['nextInputTypeSubmit', 4.374269008636475],
            ['nextInputTypeImage', 6.867544174194336],
            ['nextLoginAttrs', 0.07278082519769669],
            ['nextButtonContentContainsLogIn', -0.6560719609260559],
            ],
         "bias": -3.9029786586761475}

    Training precision: 0.9834   Recall: 1.0000                           Predicted
              Accuracy: 0.9889   95% CI: (0.9780, 0.9997)        ╭───┬── + ───┬── - ───╮
                   FPR: 0.0328   95% CI: (0.0012, 0.0644)   True │ + │    237 │      0 │
                   FNR: 0.0000   95% CI: (0.0000, 0.0000)        │ - │      4 │    118 │
                   MCC: 0.9916                                   ╰───┴────────┴────────╯

    Time per page (ms): 2 |▁▃█▅▂▁    | 34    Average per tag: 8

    Training per-tag results:
       AR_534.html  <input type="password" class="form-control pass" autocomplete="off" id="password        1.00000000
       CS_474.html  <input type="password" data-placeholder="register.password1" placeholder="Heslo"        1.00000000
                    <input type="password" data-placeholder="register.password2" placeholder="Heslo         1.00000000
       CZ_36n.html  No targets found.
       DA_177.html  <input data-validation-match="#UserModel_VerifyPassword" id="UserModel_ActionMod        0.99999964
       ...

Viewing the TensorBoard graphs with ``tensorboard --logdir runs/`` will quickly show you whether the loss function is oscillating. If you see oscilloscope-like wiggles rather than a smooth descent, the learning rate is too high: the trainer is taking steps that are too big and overshooting the optimum it's chasing. Decrease the learning rate by a factor of 10 until the graph becomes monotonically decreasing::

    fathom train samples/training  --ruleset rulesets.js --trainee yourTraineeId --learning-rate 0.1 -c tryingToRemoveOscillations

Comments added (with ``-c``) to your :doc:`fathom-train<commands/train>` calls are your friend, as a heap of anonymous TensorBoard runs otherwise quickly becomes indistinguishable.

.. note::

   Fathom currently uses the `Adam <https://en.wikipedia.org/wiki/Stochastic_gradient_descent#Adam>`_ optimization algorithm, which is good at tuning its own learning rates. Even if the loss graph oscillates at the start, it will eventually flatten out, given enough iterations. However, it's best to tamp down oscillations from the beginning so you can use validation-guided early stopping. Adam seems to dial in the learning rate quickly enough, as long as you get it within a power of 10.

   Incidentally, it's not the end of the world if some rules' scores go slightly outside [0, 1]. Limited tests have gotten away with values up to about 10 without measurable harm to training speed or accuracy. However, when feature values differ in magnitude by a factor of 1000, annoying oscillations dominate early iterations. Stick to [0, 1] for a trouble-free experience.

Once you've tamped down oscillations, use validation samples and early stopping (on by default) to keep Fathom from overfitting::

    fathom train samples/training --ruleset rulesets.js --trainee yourTraineeId --validation-set samples/validaton

The trainer comes with a variety of adjustment knobs to ensure a good fit and to trade off between false positives and false negatives. For a full tour of its capabilities, see...

:doc:`fathom train reference documentation<commands/train>`

.. _evaluating-metrics:

Evaluating Metrics
==================

:doc:`fathom train<commands/train>` and :doc:`fathom test<commands/test>` emit blocks of metrics::

    Training precision: 1.0000   Recall: 0.9083                           Predicted
              Accuracy: 0.9394   95% CI: (0.9148, 0.9639)        ╭───┬── + ───┬── - ───╮
                   FPR: 0.0000   95% CI: (0.0000, 0.0000)   True │ + │    218 │     22 │
                   FNR: 0.0917   95% CI: (0.0552, 0.1282)        │ - │      0 │    123 │
                   MCC: 0.8778                                   ╰───┴────────┴────────╯

Here's how to read them:

* `Precision and recall <https://en.wikipedia.org/wiki/Precision_and_recall>`_ are all you really need to look at. If tweaking a ruleset improves those, keep the tweak. For most applications, one or the other will be more important. For example, for autofill of saved passwords, it's more important to be precise so you don't accidentally put a password into, say, a blog comment field. Remember you can trade off between the two values with :doc:`fathom train<commands/train>`'s ``-p`` option.
* Ignore Accuracy, which can be misleading for problems with unbalanced classes. For example, if you're trying to identify paragraphs containing author bios and those are rare in the space of all paragraphs, a ruleset could simply say "No, that's not a bio" all the time and have high accuracy. It would, however, have zero recall and be utterly useless.
* FNR (false-negative rate) and FPR (`false-positive rate <https://en.wikipedia.org/wiki/False_positive_rate>`_) are defined in the standard way and are provided for people familiar with them.
* MCC (`Matthews Correlation Coefficient <https://en.wikipedia.org/wiki/Matthews_correlation_coefficient>`_) tries to mix down all sources of error into one number. It's best to look at precision and recall instead, as they are usually not equally important. However, if you need a single number to roughly sort a bunch of candidate models, MCC is as good a choice as any. It ranges from -1 (getting exactly the wrong predictions all the time) through 0 (predictions having no correlation with the truth) to 1 (a perfect predictor).
* All of these statistics (and others, if you like) can be computed from the raw `confusion matrix <https://en.wikipedia.org/wiki/Confusion_matrix>`_, contained in the bordered box to the right. It shows you raw numbers of false positives, false negatives, true positives, and true negatives.

There are also speed histograms::

    Time per page (ms): 2 |  ▃█▃▁▁   | 35    Average per tag: 11

These show how much time Fathom is taking per page and per tag. The horizontal axis is milliseconds, and the vertical is page count. The histograms vary more from run to run than the other (convergent) statistics, and, of course, the absolute numbers change based on the speed of the machine. What you should look out for is the sudden appearance of large bars to the far right (indicating many slow outliers) or a drastic increase in the numbers (indicating you slowed things down across the board).

Workflow
========

A sane authoring process is a feedback loop something like this:

#. Collect samples. Observe patterns in the :term:`target` nodes as you do.
#. Write a few rules based on your observations.
#. Run the trainer. Start with 10-20 training pages and an equal number of validation ones.
#. Examine *training* precision and recall. (See :ref:`Evaluating Metrics <evaluating-metrics>`.) If they are insufficient, examine the failing training pages. The trainer will point these out on the commandline, but FathomFox's Evaluator will help you track down ones that are hard to distinguish from their tag excerpts. Remediate by changing or adding rules. If there are signals Fathom is missing—positive or negative—add rules that score based on them. You'll probably also need to do some :doc:`debugging`.
#. Go back to step 3.
#. Once *validation* precision and recall are sufficient, use :doc:`fathom test<commands/test>` on a fresh set of *testing* samples. These are your *testing metrics* and should reflect real-world performance, assuming your sample size is large and representative enough. The computed 95% confidence intervals should help you decide the former.
#. If testing precision and recall are too low, imbibe the testing pages into your training set, and go back to step 3. As typical in supervised learning systems, testing samples should be considered "burned" once they are measured against a single time, as otherwise you are effectively training against them. Samples are precious.
#. If testing precision and recall are sufficient, you're done! Paste the trained coefficients and biases into your ruleset, paste your ruleset into your application, and ship it.
