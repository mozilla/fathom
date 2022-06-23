===========
Ruleset Zoo
===========

Welcome to the Fathom Ruleset Zoo, a bestiary of Fathom real-world examples. Each gives an overview and links to a repository with full source code.

.. note::
   Some repos are private because they contain copyrighted training samples. While we believe this is fair use, we don't wish to provoke cease-and-desist bots. If you work for Mozilla, just ask, and we’ll grant you access. Otherwise, we've pasted the ruleset source code into the docs, so you can at least see that. Enjoy!

New-Password Forms
==================

Firefox's password manager needed a way to identify new-password fields so it could suggest (and memorize) high-entropy passwords for them. There is standardized markup for this, but only 2-4% of sites use it. Fathom thus stepped in to backstop the other 97%. On a corpus of 508 pages, we trained to a testing precision of 99.2% and recall of 92.1%. (We used ``fathom train --pos-weight`` to slant the results in favor of fewer false positives, sacrificing some recall for it.) Independent QA work showed an accuracy and false-negative rate better than that of Google Chrome—and a false-positive rate only 1% worse—and all of that with a purely client-side model. It shipped in Firefox 76.

:doc:`Ruleset source<zoo/new_password>`

`Full repo <https://github.com/mozilla-services/fathom-login-forms/blob/master/new-password/rulesets.js>`_

Login Forms
===========

As a proof-of-concept next-generation autofiller for `Firefox Lockwise <https://www.mozilla.org/en-US/firefox/lockwise/>`_, we built recognizers for login forms’ username fields and Log In buttons.

This is a clean, simple example of a Fathom 3 ruleset. It was designed for Fathom 3 from the beginning, solves the problem concisely, and has respectable accuracy.

Recognizers
-----------

* **Username field.** This is the username or (as is increasingly the case) email field of the login form. The ruleset finds the precise ``<input>`` element for form fill. Validation precision and recall: both 96.6%, on 162 candidate tags across 64 pages, including ones with no login forms or with adversarial constructs like password-change, credit-card, and shipping forms.
* **Next button.** The Log In button or, for multi-page login flows, whatever you click to advance to the next step. This was the more challenging recognizer, since there is a wider diversity of both markup and text for these constructs. Validation precision: 100%. Validation recall: 72.9%. This is across 490 candidate tags on 64 pages. There is plenty of signal left on the table, so more invested time should give us another percentage point or two. (The whole project was timeboxed to about 3 weeks.)

:doc:`Ruleset source<zoo/login>`

`Full repo <https://github.com/mozilla-services/fathom-login-forms/blob/master/lockwise-proof-of-concept/trainees.js>`_

Smoot: Page Classification
==========================

An upcoming Firefox metrics effort, Project Smoot will use a set of whole-page classifiers to characterize user tasks in a privacy-preserving way.

Recognizers
-----------
* **Shopping.** A page is a shopping page iff a user would seek it out in the process of choosing or buying things. This is a very challenging rubric, as it almost demands the model reach inside the head of the user to determine intent. A page about Amazon's affiliate program is not a shopping page, even though it appears on a shopping-focused domain. A forum thread on Reddit discussing the merits of competing products is a shopping page, even though it’s not near any actual Buy buttons.

  Despite the difficulty of the task, our model, still under development, scores over 90% in validation on a corpus of 100 pages.
* **Article.** A page whose main attraction is prose to read. Though still under development, this model scores 90% in validation on a corpus of 60 pages.
* **“Techie” Article.** An article aimed at a computer-savvy audience. This is intended for audience segmentation. It’s too early for numbers here as well.

:doc:`Articles ruleset source<zoo/smoot_articles>`

:doc:`Shopping ruleset source<zoo/smoot_shopping>`

`Full repo <https://github.com/mozilla-services/fathom-smoot>`_

Price Tracker
=============

Originally designed for Fathom 2.0 but ported to 3.0 as a team familiarization exercise, Firefox Price Tracker is a now-retired web extension that periodically polled the prices of a wishlist of products and notified the user of price drops. Fathom provided the recognition of products for sale: their names, images, and prices. Out of an abundance of caution, Price Tracker underutilized Fathom’s ability to generalize, artificially limiting itself to the 5 top commerce sites in the U.S. However, its compact example is easy to digest in a sitting, and it’s a fine instance of Fathom increasing the agency of thousands of users when wrapped in a quality, lightweight UI.

.. image:: img/price_tracker_screenshot.png

Recognizers
-----------

* **Image.** The “hero” image showing the product. Validation accuracy: 99.34%. Testing accuracy: 75%.
* **Title.** The name of the product. Validation accuracy: 100%. Testing accuracy: 83.38%.
* **Price.** The price charged for the product. Validation accuracy: 99.27%. Testing accuracy: 99.46%.

Price Tracker’s accuracy numbers are unusually noisy, partly due to the rules being written with an earlier version of Fathom in mind and partly due to its small, homogeneous sample corpus. Pages came from only 5 sites, and testing and validation corpora were each only 20 pages. The 95% confidence interval for accuracy numbers thus spans as much as 30%. If we were to ship a Fathom-3.0-powered Price Tracker, we would refine until we had only a few percentage points of spread.

More metrics are available on `the pull request that merged the Fathom 3 upgrade <https://github.com/mozilla/price-tracker/pull/317>`_, but they mostly serve as a warning that a more diverse corpus is necessary for confident measurement. Take Price Tracker as an example of coding practices and product-market fit, not corpus design.

:doc:`Ruleset source<zoo/price_tracker>`

`Full repo <https://github.com/mozilla/price-tracker/blob/master/src/extraction/fathom/ruleset_factory.js>`_

Pop-up Detector
===============

Pop-up “windows” on the web have migrated from actual windows to in-page elements, largely due to browsers’ success at blocking the old kind. We mentored a student project to recognize in-page pop-ups using the older Fathom 2.

Results were encouraging, hovering around 85% on a blind testing corpus. Revamped for a modern Fathom, it might give higher numbers with little effort. In the meantime, it serves as a good example of perceptive rules. But don't lean overmuch on the ranges of numbers returned from scoring callbacks; that all changed in Fathom 3.

`Pop-up Detector source <https://github.com/capstone-2018873/fathom-trainees/tree/master/src/models>`_
