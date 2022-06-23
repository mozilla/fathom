==================
Collecting Samples
==================

Labeled samples are one of the two inputs that go into a working Fathom recognizer. By being statistically representative of the pages your application expects to encounter, they teach the trainer how to balance the contributions of the rules in the ruleset. Corpus collection is the process of selecting pages, labeling example elements on them, and serializing and organizing them in a repository for later training and testing.

Suggested Directory Structure
=============================

Labeled samples are best stored in a version control repository next to the ruleset you're developing. This allows you to go back and forth in time to reproduce results and correct labeling errors. Here's the layout we recommend:

.. code-block:: none

    samples/
        unused/
            foo.com.html   -- A positive sample, which contains an example of what we're looking for
            bar.com.html
            baz.net.html
            qux.com.N.html  -- A negative ("N") page: one that does NOT contain what we're looking for
            corge.com.N.html
            grault.de.N.html
            ...
        training/
            waldo.com.html
            fred.org.N.html
            foo.com.2.html  -- Add a 2 so it doesn't conflict with foo.com.html if they ever end up in the same folder
            ...
        validation/
        testing/
        rubric.txt
    rulesets.js       -- Ruleset code

Note the ".N" suffix that identifies negative pages. While Fathom does use any unlabeled :term:`candidate` elements as negative samples, the convention of signifying negative-only pages by name saves the trouble of double checking when the trainer advises that it can't find any labeled elements in a file. Negative samples, whether or not they need dedicated pages brought in to provide them, are vital for teaching Fathom to avoid false positives.

Rubrics
=======

Note the ``rubric.txt`` file in the ``samples/`` directory. Having a written standard for what to label is key to a good result; if samples are labeled inconsistently, they will push the trainer in conflicting directions, and your accuracy will suffer.

Be sure to keep your rubrics up to date. Whenever you encounter a case where you have to make a new decision—something the rubric doesn't already clearly specify—codify that decision so you are consistent with it in the future. Check your rubrics into version control so they change atomically with the samples whose labeling they describe.

Collecting
==========

With a first draft of your rubric written, you're ready to collect samples using FathomFox (:ref:`see installation instructions <fathomfox-installation>`).

1. Use Firefox’s Responsive Design mode (command-option-M) to set a repeatable window size. 1366x768 is most representative of desktop browsing habits at the moment. Using a consistent size will ensure that the proper CSS and images (which may be driven by media queries) will be frozen and later reloaded with the page.
2. Navigate to a web page that contains an example of what you’re trying to recognize: for instance, a background overlay behind a modal dialog, as the stock example ruleset seeks out.
3. Right-click the element, and choose Inspect Element. If you didn't quite get the right element by cicking, fine-tune your selection using the developer tools’ Inspector.
4. Switch to the Fathom developer tools tab, and enter a label of your choice (like "overlay" in this case) in the label field.
5. Click Save Page. FathomFox “freezes” the page, inlining images and CSS into data URLs and getting rid of JS to keep pages deterministic for repeated training or testing. (Scripts loading scripts loading other scripts is surprisingly common in the wild, which often makes pages turn out unpredictably, not to mention being dependent on the network.) If you are unable to capture the page while the labeled elements are showing because they are triggered by a hover state, you can press `Ctrl+Shift+O` to trigger a save without moving the mouse.
6. Put the page into the ``unused`` folder in your repository for now.
7. Repeat until you have at least 20 pages. This is about the minimum necessary to run the trainer usefully; depending on the difficulty of your problem, you may need on the order of hundreds.

.. note::

   There is also a bulk Corpus Collector tool, accessible from the toolbar button. Enter some URLs, and it freezes the pages one after another in the same way the dev tools panel does. The Corpus Collector is useful for grabbing hundreds of pages at once, but it doesn’t give you the opportunity to stop and label or interact with each (though it can scroll to the bottom or wait a predetermined time before freezing). Generally, page-by-page collection is the better choice.

Storing Samples in Git
======================

There are great advantages to storing samples in version control. However, corpora often bump up against the limits imposed by git hosting services like GitHub. Thus, we recommend using `Git Large File Storage (LFS) <https://git-lfs.github.com/>`_ to store samples. This is facilitated by :doc:`fathom extract<commands/extract>`, which breaks large subresources like images back out of the HTML. As a bonus, your HTML files will shrink drastically and become feasible to diff and load into text editors.

Using fathom extract
--------------------

:doc:`fathom extract<commands/extract>` pulls the inlined data URLs representing subresources (like images and CSS) out of your samples, converts them into images and CSS files, places them in a newly created sample-specific directory within a newly created resources directory, and replaces the data URLs with references to the new files. This let you use Git-LFS to store the new subresource files.

For example, if you have this directory of samples: ::

    samples/
        unused/
            foo.com.html
            bar.edu.html
            baz.com.html
            ...

Running... ::

    fathom extract samples/unused

will change your directory to: ::

    samples/
        unused/
            originals/
            resources/
                foo.com/
                    1.png
                    2.css
                    3.css
                    ...
                bar.edu/
                    1.css
                    2.jpg
                    3.jpg
                    ...
                baz.com/
                    1.css
                    2.png
                    3.jpg
                    ...
                ...
            foo.com.html
            bar.edu.html
            baz.com.html
            ...

Once you are comfortable that your samples extracted correctly, you can delete the ``originals`` directory.

Configuring Git-LFS
-------------------

Next, follow the `Git-LFS Getting Started steps <https://git-lfs.github.com/>`_ to keep your new resources directories in large-file storage. However, in step 2, instead of running the ``git lfs track`` command, it is easier to directly edit the ``.gitattributes`` file. For our suggested directory structure, you would add the line… ::

    samples/**/resources/** filter=lfs diff=lfs merge=lfs -text

The first ``/**`` ensures all sample directories (``unused``, ``training``, etc.) are tracked, and the second ``/**`` ensures the subdirectories are tracked.

Training, Testing, and Validation Sets
======================================

Up to now, we've kept the samples in the ``unused`` folder. Now it's time to divide them among the training, validation, and testing sets using :doc:`fathom pick<commands/pick>`. This command randomly moves a given number of files from one directory to another to keep the sets mutually representative.

A training set on the order of a few hundred samples is generally sufficient to push precision and recall percentages into the high 90s. You'll want additional samples for a validation set (to let the trainer know when it's begun to overfit) and a test set (to come up with final accuracy numbers). We recommend a 60/20/20 split among training/validation/testing sets. This gives you large enough validation and testing sets, at typical corpus sizes, while shunting as many samples as possible to the training set so you can mine them for rule ideas.

For example, if you had collected 100 samples initially, you would run these commands to divide them into sets::

    cd samples
    fathom pick unused training 60
    fathom pick unused validation 20
    fathom pick unused testing 20

If you collected a great many samples, leave some in the ``unused`` folder for now; the trainer will run faster with less data. Work on your ruleset until you have high accuracy on a few dozen samples, and only then add more.

Maintaining Representativeness
------------------------------

It's important to keep your sets mutually representative. If you have a collection of samples sorted by some metric, like site popularity or when they were collected, don't use samples 1-100 for training and then 101-200 for validation. Instead, use :command:`fathom pick` to proportionally assign them to sets: 60% to training and 20% to each of validation and testing. You can repeat this as you later come to need more samples.
