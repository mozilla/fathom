============
Introduction
============

Fathom is a supervised-learning system for recognizing parts of web pages—pop-ups, address forms, slideshows—or for classifying a page as a whole. A DOM flows in one side, and DOM nodes flow out the other, tagged with types and probabilities that those types are correct. A Prolog-like language makes it straightforward to specify the hints that suggest each type, and a neural-net-based trainer determines the optimal contribution of each. Finally, the `FathomFox <https://addons.mozilla.org/en-US/firefox/addon/fathomfox/>`_ web extension and a rich assortment of commandline tools help you collect, label, and use a corpus of web pages to train a recognizer.

Why?
====

A study of existing projects like Readability and Distiller suggests that purely imperative approaches to semantic extraction get bogged down in the mechanics of DOM traversal and state accumulation, obscuring the operative parts of the extractors and making new ones long and tedious to write. They involve a lot of human guessing of numerical weights. And they are brittle due to the promiscuous profusion of state. Fathom makes extractors easier to write by providing a declarative language, corpus capture, and neural-net-based training. With these, Fathom handles tree-walking, execution order, weight determination, and annotation bookkeeping, letting you concentrate on your application.

Specific Areas We Address
=========================

* Browser-native DOM nodes are mostly immutable, and ``HTMLElement.dataset`` is string-typed, so storing arbitrary intermediate data on nodes is clumsy. Fathom addresses this by providing the Fathom node (or :term:`fnode`, pronounced fuh-NODE), a proxy around each DOM node which we can scribble on.
* With imperative extractors, any experiments or site-specific customizations must be hard-coded in. On the other hand, Fathom's :term:`rulesets<ruleset>` (the programs you write in Fathom) are unordered and thereby decoupled, stitched together only by the :term:`types<type>` they consume and emit. External rules can thus be plugged into existing rulesets, making it easy to experiment without maintaining a fork—or to provide dedicated rules for particularly intractable web sites.
* Types provide an easy way to categorize DOM nodes. They are also Fathom's black-box units of abstraction, as functions are in other programming languages.
* The type system also makes explicit the division between a ruleset's public and private APIs: the types are public, and the imperative activity that goes on inside callback functions is private. This provides the freedom to extend existing rulesets without editing them directly, so multiple third-party refinements can be mixed together.
* Persistent state is cordoned off in typed :term:`notes<note>` on fnodes. Thus, when a rule declares that it takes such-and-such a type as input, it can rightly assume (if rules are written consistently) there will be a note of that type on the fnodes that are passed in.
* A :doc:`neural-network-powered trainer<training>` quickly adjusts the weights of your rules to maximize accuracy.

Bonus Features
--------------

* Efficient execution, driven by a query planner that understands inter-rule dependencies
* Lazy execution, so you can have arbitrarily large rulesets with impunity
* Caching to keep from re-deriving intermediate results between queries
* Clustering based on a notion of DOM node distance influenced by structural similarity
* Many handy utils from which to compose scoring callbacks

Where It Works
==============

Fathom is a JavaScript framework that works against the DOM API, so you can use it server-side with ``jsdom`` or any other implementation, or you can embed it in a browser and pass it a native DOM.
