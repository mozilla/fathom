========
Glossary
========

.. glossary::

   candidate
       Any node (:term:`target` or not) brought into the ruleset by a :func:`dom` or :func:`element` call for consideration

   fnode
       A wrapper around a DOM node, holding :term:`scores<score>`, :term:`notes<note>`, and :term:`types<type>` pertaining to it. See :doc:`fnodes`.

   note
       An arbitrary, opaque-to-Fathom piece of data attached to a given :term:`type` on a :term:`fnode`. Notes can be consulted by scoring callbacks and are a good place to park expensive-to-recompute information. They are the main way of passing data between rules.

   ruleset
       The unordered collection of rules that forms a Fathom program. See :doc:`rules` for more on the relationships between top-level constructs.

   score
       The fuzzy-edged part of :term:`fnode` state. A floating-point number, typically between 0 and 1, attached to a certain :term:`type` on a :term:`fnode`. They represent the confidence with which a node belongs to a type.

   subscore
       A single rule's contribution to a node's score for some type. In Fathom's current incarnation as a series of (single-layer) perceptrons, each rule's subscore is multiplied by a coefficient, which is derived from training. The weighted subscores are then added together and fed through a sigmoid function to get the final score for a node for a type.

   target
       A "right answer" DOM node, one that should be recognized as belonging to some type

   type
       A string-typed category assigned to a :term:`fnode`. Types are the boolean, hard-edged, enumerated parts of fnode state. They also largely determine inter-rule dependencies and thus which rules get run in response to a query.

   vectorize
       To turn a collection of sample HTML pages into vectors of numbers which the trainer then imbibes.
