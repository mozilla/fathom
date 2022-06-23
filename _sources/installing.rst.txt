==========
Installing
==========

Fathom consists of 3 parts. Here's how to install each one.

.. _fathomfox-installation:

Commandline Tools
=================

Fathom's commandline tools take your labeled pages as input and train the machine-learning model. They also contain an embedded copy of FathomFox (see below), the simplest way to collect pages. If you don't already have Python 3.7 or better, download it from https://www.python.org/downloads/. Then, install the tools by running... ::

    pip3 install fathom-web

It's possible your Python package manager is called simply "pip" rather than "pip3". Give that a try if the above fails.

You will also need to install `Node.js <https://nodejs.org/en/>`_ to use many of the commandline tools.

FathomFox
=========

FathomFox is a browser extension used to label web pages. The best way to get it is to first install the commandline tools and then run… ::

    fathom fox

This will launch a built-in copy of FathomFox in a fresh Firefox profile so ad blockers and other customizations don't interfere with the clean capture of labeled pages. (Some ad blockers will make changes to the DOM, like adding style attributes to ad iframes to hide them.) Using the commandline launcher also lets you pass in your own rulesets for debugging with the FathomFox Evaluator. See the ``-r`` option on the :doc:`fathom fox reference page<commands/fox>`.

For more casual use, you can instead `install FathomFox through the web <https://addons.mozilla.org/en-US/firefox/addon/fathomfox/>`_, in which case it will be your responsibility to avoid addons that might mutate the DOM.

Fathom
======

Fathom proper is a JS library which runs trained rulesets to do the actual recognition. You don't need to worry about installing it until your rulesets are performing satisfactorily and you're ready to integrate them with your application.

If your application runs server-side under `Node.js <https://nodejs.org/en/>`_, you can install `the Fathom node package <https://www.npmjs.com/package/fathom-web>`_ like any other dependency::

    npm install fathom-web

If, instead, you're working on a Firefox feature, you can use the copy of Fathom already in Firefox by saying something like this at the top of the file containing your ruleset::

    ChromeUtils.defineModuleGetter(
      this,
      "fathom",
      "resource://gre/modules/third_party/fathom/fathom.jsm"
    );

    const {
      dom,
      element,
      out,
      rule,
      ruleset,
      score,
      type,
      utils: { identity, isVisible, min },
      clusters: { euclidean },
    } = fathom;

Finally, if you need a self-contained bundle of Fathom in a context that can't use node packages, check out our `source <https://github.com/mozilla/fathom>`_ and run ``make -C fathom bundle``. This creates the bundle at ``fathom/dist/fathom.js``.
