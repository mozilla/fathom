==================
Rules and Rulesets
==================

Most everything on this page is a top-level object in the Fathom library, importable like this, for instance:

.. code-block:: js

   const {
      dom,
      element,
      out,
      rule,
      ruleset
    } = require('fathom-web');

Rulesets
========

The most important Fathom object is the ruleset, an unordered collection of rules. The plain old :class:`Ruleset` is what you typically construct, via the ``ruleset`` convenience function:

.. autofunction:: ruleset

.. autoclass:: Ruleset
   :members: against, rules

Then you call :func:`Ruleset.against` to get back a :class:`BoundRuleset`, which is specific to a given DOM tree. From that, you pull answers.

.. autoclass:: BoundRuleset
   :members: get, setCoeffsAndBiases

Rules
=====

These are the control structures which govern the flow of scores, types, and notes through a ruleset. You construct a rule by calling :func:`rule` and passing it a left-hand side and a right-hand side:

.. autofunction:: rule

.. _lhs:

Left-hand Sides
---------------

Left-hand sides are currently a few special forms which select nodes to be fed to right-hand sides.

.. autofunction:: dom

.. autofunction:: lhs.element
   :short-name:

.. function:: type(theType)

   Take nodes that have the given type. Example: ``type('titley')``

   .. autofunction:: TypeLhs#max
      :short-name:

   .. autofunction:: TypeLhs#bestCluster
      :short-name:

.. autofunction:: and(typeCall[, typeCall, ...])

.. autofunction:: nearest(typeCallA, typeCallB[, distance=euclidean])

.. autofunction:: when(predicate)


Right-hand Sides
----------------

A right-hand side takes the nodes chosen by the left-hand side and mutates them. Spelling-wise, a RHS is a strung-together series of calls like this::

    type('smoo').props(someCallback).type('whee').score(2)

To facilitate factoring up repetition in right-hand sides, calls layer together like sheets of transparent acetate: if there are repeats, as with ``type`` in the above example, the rightmost takes precedence and the left becomes useless. Similarly, if :func:`props`, which can return multiple properties of a fact (element, note, score, and type), is missing any of these properties, we continue searching to the left for anything that provides them (excepting other :func:`props` calls—if you want that, write a combinator, and use it to combine the 2 functions you want)). To prevent this, return all properties explicitly from your props callback, even if they are no-ops (like ``{score: 1, note: undefined, type: undefined}``). Aside from this layering precedence, the order of calls does not matter.

A good practice is to use more declarative calls—:func:`score`, :func:`note`, and :func:`type`—as much as possible and save :func:`props` for when you need it. The query planner can get more out of the more specialized calls without you having to tack on verbose hints like :func:`atMost` or :func:`typeIn`.

.. autofunction:: InwardRhs#atMost
   :short-name:

.. autofunction:: InwardRhs#props
   :short-name:

   For example...

   .. code-block:: js

      function callback(fnode) {
          return [{score: 3,
                   element: fnode.element,  // unnecessary, since this is the default
                   type: 'texty',
                   note: {suspicious: true}}];
      }

   If you use ``props``, Fathom cannot look inside your callback to see what type you are emitting, so you must declare your output types with :func:`typeIn` or set a single static type with ``type``. Fathom will complain if you don't. (You can still opt not to return any type if the node turns out not to be a good match, even if you declare a :func:`typeIn`.)

.. autofunction:: InwardRhs#note
   :short-name:

   Since every node can have multiple, independent notes (one for each type), this applies to the type explicitly set by the RHS or, if none, to the type named by the `type` call on the LHS. If the LHS has none because it's a `dom(...)` LHS, an error is raised.

   When you query for fnodes of a certain type, you can expect to find notes of any form you specified on any RHS with that type. If no note is specified, it will be undefined. However, if two RHSs emits a given type, one adding a note and the other not adding one (or adding an undefined one), the meaningful note overrides the undefined one. This allows elaboration on a RHS's score (for example) without needing to repeat note logic.

   Indeed, ``undefined`` is not considered a note. So, though notes cannot in general be overwritten, a note that is ``undefined`` can. Symmetrically, an ``undefined`` returned from a :func:`note` or :func:`props` or the like will quietly decline to overwrite an existing defined note, where any other value would cause an error. Rationale: letting ``undefined`` be a valid note value would mean you couldn't shadow a leftward note in a RHS without introducing a new singleton value to serve as a "no value" flag. It's not worth the complexity and the potential differences between the (internal) fact and fnode note value semantics.

   Best practice: any rule adding a type should apply the same note. If only one rule of several type-foo-emitting ones did, it should be made to emit a different type instead so downstream rules can explicitly state that they require the note to be there. Otherwise, there is nothing to guarantee the note-adding rule will run before the note-needing one.

.. autofunction:: out

   If you are not using ``through()`` or ``allThrough()``, you can omit the call to ``out()`` and simply use specify the key as the RHS of the rule. For example: ``rule(type('titley').max(), out('title'))`` can be written as ``rule(type('titley').max(), 'title')``.

   .. autofunction:: OutwardRhs#through
      :short-name:

   .. autofunction:: OutwardRhs#allThrough
      :short-name:

.. autofunction:: InwardRhs#score
   :short-name:

.. autofunction:: InwardRhs#type
   :short-name:

.. autofunction:: InwardRhs#typeIn(type[, type, ...])
   :short-name:
